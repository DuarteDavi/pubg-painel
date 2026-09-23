from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
from app.database import get_db
from app.schemas import LoginRequest, LoginResponse, VerifyResponse, TokenResponse, RefreshTokenRequest, VerifyRequest
from app.models import Client, License, LicenseDevice, ClientSession, Product, ClientStatus
from app.auth import (
    verify_password, hash_password, create_access_token, create_refresh_token,
    verify_token, hash_token, hash_device, get_current_timestamp_utc
)
from app.utils import record_audit_log, is_rate_limited, record_login_attempt, verify_client_session, get_client_ip
from app.models import AuditAction

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Client login endpoint.
    Validates credentials, product, device, and license.
    BACKEND VALIDATION: Never trust client data about license or permissions.
    """
    ip_address = get_client_ip(request)

    # Rate limiting
    if is_rate_limited(f"client_{request_data.login}"):
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, client_id=None,
            details="Rate limited", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMITED")

    # Validate product exists
    product = db.query(Product).filter(Product.name == request_data.product).first()
    if not product:
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, details="Invalid product",
            ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_PRODUCT")

    # Validate client
    client = db.query(Client).filter(Client.login == request_data.login).first()
    if not client or not verify_password(request_data.password, client.password_hash):
        record_login_attempt(f"client_{request_data.login}")
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, details="Invalid credentials",
            ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    # Validate client status
    if client.status != ClientStatus.ACTIVE:
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, client_id=client.id,
            details=f"Client status: {client.status}", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LICENSE_DISABLED")

    # Validate license
    license_obj = db.query(License).filter(
        and_(
            License.client_id == client.id,
            License.product_id == product.id,
        )
    ).first()

    if not license_obj or not license_obj.is_active:
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, client_id=client.id,
            details="No license or license disabled", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LICENSE_DISABLED")

    # Validate license expiry
    now = get_current_timestamp_utc()
    if license_obj.expires_at < now:
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, client_id=client.id,
            details="License expired", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LICENSE_EXPIRED")

    # Hash device (never store original hardware serials)
    device_hash = None
    if request_data.device:
        device_hash = hash_device(request_data.device)

    if not device_hash:
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, client_id=client.id,
            details="Invalid device hash", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_DEVICE")

    # Check if device already linked
    existing_device = db.query(LicenseDevice).filter(
        and_(
            LicenseDevice.license_id == license_obj.id,
            LicenseDevice.device_hash == device_hash,
        )
    ).first()

    if existing_device:
        # Same device, just update last seen
        existing_device.last_seen_at = now
        existing_device.last_ip = ip_address
        device_id = str(existing_device.id)
    else:
        # New device - check limit with transaction isolation
        # Use FOR UPDATE to lock the row and prevent race conditions
        license_obj = (
            db.query(License)
            .filter(License.id == license_obj.id)
            .with_for_update()
            .one()
        )

        # Recount after lock to ensure accuracy (device could have been added between check and lock)
        device_count = db.query(LicenseDevice).filter(
            LicenseDevice.license_id == license_obj.id
        ).count()

        if device_count >= license_obj.device_limit:
            record_audit_log(
                db, AuditAction.DEVICE_LIMIT_REACHED, client_id=client.id,
                resource_type="license", resource_id=str(license_obj.id),
                details=f"Device limit reached: {device_count}/{license_obj.device_limit}",
                ip_address=ip_address, success=False
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="DEVICE_LIMIT_REACHED")

        # Create new device within the lock
        new_device = LicenseDevice(
            license_id=license_obj.id,
            client_id=client.id,
            device_hash=device_hash,
            device_name=request_data.device.get("device_name", "Unknown"),
            last_ip=ip_address,
            last_seen_at=now,
        )
        db.add(new_device)
        db.flush()
        device_id = str(new_device.id)

    # Update last login
    client.last_login_at = now

    # Create tokens
    access_token = create_access_token({"sub": client.login, "client_id": client.id})
    refresh_token = create_refresh_token({"sub": client.login, "client_id": client.id})

    # Store session
    session = ClientSession(
        client_id=client.id,
        token_hash=hash_token(access_token),
        refresh_token_hash=hash_token(refresh_token),
        expires_at=now + __import__('datetime').timedelta(minutes=15),
        refresh_expires_at=now + __import__('datetime').timedelta(days=7),
        device_hash=device_hash,
    )
    db.add(session)

    db.commit()

    # Audit log
    record_audit_log(
        db, AuditAction.CLIENT_LOGIN, client_id=client.id,
        resource_type="device", resource_id=device_id,
        ip_address=ip_address, success=True
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        login=client.login,
        expires_at=now + __import__('datetime').timedelta(minutes=15),
        license_expires_at=license_obj.expires_at,
        device_id=device_id,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify_session(verify_req: VerifyRequest, request: Request, db: Session = Depends(get_db)):
    """
    Verify client session validity with device binding.
    BACKEND VALIDATION: Check everything - token, client, license, device binding.
    Extracts Bearer token from Authorization header.
    Device hash must match the device that created the session (device vínculo).
    Rate limited to prevent token enumeration attacks.
    """
    ip_address = get_client_ip(request)
    rate_limit_key = f"verify_{ip_address}"

    # Rate limiting on IP to prevent brute force
    if is_rate_limited(rate_limit_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMITED")

    # Extract Bearer token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        record_login_attempt(rate_limit_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MISSING_BEARER_TOKEN")

    token = auth_header[7:]  # Remove "Bearer " prefix

    # Decode token
    payload = verify_token(token)
    if not payload:
        record_login_attempt(rate_limit_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SESSION_REVOKED")

    client_id = payload.get("client_id")
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client or client.status != ClientStatus.ACTIVE:
        record_login_attempt(rate_limit_key)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LICENSE_DISABLED")

    # Validate session in database
    session_data = verify_client_session(hash_token(token), db)
    if not session_data:
        record_login_attempt(rate_limit_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SESSION_REVOKED")

    # DEVICE VÍNCULO: Validate device hash matches session device (prevent token theft on other machines)
    # Calculate fingerprint using same method as login
    verification_device_hash = hash_device({
        "machine_guid_hash": verify_req.device_hash,
    })

    if session_data.get("device_hash") != verification_device_hash:
        record_audit_log(
            db, AuditAction.CLIENT_LOGIN_FAILED, client_id=client.id,
            details="Device mismatch during session verification",
            ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="DEVICE_MISMATCH")

    # Validate license
    license_obj = db.query(License).filter(
        License.client_id == client.id
    ).first()

    if not license_obj or not license_obj.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LICENSE_DISABLED")

    now = get_current_timestamp_utc()
    if license_obj.expires_at < now:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="LICENSE_EXPIRED")

    return VerifyResponse(
        valid=True,
        login=client.login,
        expires_at=session_data["expires_at"],
        license_expires_at=license_obj.expires_at,
        device_id=str(session_data.get("device_hash", "")),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access(request_data: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    Implements refresh token rotation (new refresh token on each use).
    """
    ip_address = get_client_ip(request)

    payload = verify_token(request_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SESSION_REVOKED")

    client_id = payload.get("client_id")
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SESSION_REVOKED")

    # Create new tokens
    new_access_token = create_access_token({"sub": client.login, "client_id": client.id})
    new_refresh_token = create_refresh_token({"sub": client.login, "client_id": client.id})

    # Update session with new tokens (refresh token rotation)
    now = get_current_timestamp_utc()
    session = db.query(ClientSession).filter(
        ClientSession.refresh_token_hash == hash_token(request_data.refresh_token)
    ).first()

    if session:
        session.token_hash = hash_token(new_access_token)
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.expires_at = now + __import__('datetime').timedelta(minutes=15)
        session.refresh_expires_at = now + __import__('datetime').timedelta(days=7)
        db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_at=now + __import__('datetime').timedelta(minutes=15),
    )


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """
    Revoke client session.
    Extracts Bearer token from Authorization header.
    """
    # Extract Bearer token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MISSING_BEARER_TOKEN")

    token = auth_header[7:]  # Remove "Bearer " prefix

    from app.utils import revoke_client_session
    revoke_client_session(hash_token(token), db)
    return {"message": "Logged out"}
