from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.schemas import (
    AdminLoginRequest, AdminLoginResponse, ClientCreate, ClientResponse,
    ClientUpdate, ClientListResponse, DashboardStats, AuditLogResponse, DeviceResponse,
    LicenseResponse
)
from app.models import (
    Client, License, LicenseDevice, AdminSession, Product, AuditLog, ClientStatus,
    LicenseType, AuditAction
)
from app.auth import (
    verify_password, hash_password, create_access_token, hash_token,
    verify_token, verify_admin_password, get_current_timestamp_utc
)
from app.utils import (
    record_audit_log, is_rate_limited, record_login_attempt, verify_admin_session,
    revoke_admin_session, get_client_ip
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_token(token: str, db: Session = Depends(get_db)) -> dict:
    """
    Dependency: Verify admin token is valid.
    BACKEND VALIDATION: Always check token in database.
    """
    payload = verify_token(token)
    if not payload or payload.get("type") == "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    token_hash = hash_token(token)
    if not verify_admin_session(token_hash, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

    return payload


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request_data: AdminLoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Admin login.
    BACKEND VALIDATION: Check admin credentials against .env config.
    Rate limited: 5 attempts per 15 minutes.
    """
    ip_address = get_client_ip(request)

    # Rate limiting
    if is_rate_limited("admin_login"):
        record_audit_log(
            db, AuditAction.ADMIN_LOGIN_FAILED,
            details="Rate limited", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMITED")

    # Validate credentials
    if request_data.login != __import__('app.config', fromlist=['settings']).settings.admin_login:
        record_login_attempt("admin_login")
        record_audit_log(
            db, AuditAction.ADMIN_LOGIN_FAILED,
            details="Invalid login", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    if not verify_admin_password(request_data.password):
        record_login_attempt("admin_login")
        record_audit_log(
            db, AuditAction.ADMIN_LOGIN_FAILED,
            details="Invalid password", ip_address=ip_address, success=False
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    # Create token
    token = create_access_token({"type": "admin"})
    now = get_current_timestamp_utc()

    # Store session
    from app.config import settings
    session = AdminSession(
        token_hash=hash_token(token),
        expires_at=now + timedelta(hours=settings.session_expiration_hours),
        ip_address=ip_address,
    )
    db.add(session)
    db.commit()

    # Audit log
    record_audit_log(
        db, AuditAction.ADMIN_LOGIN,
        ip_address=ip_address, success=True
    )

    return AdminLoginResponse(
        access_token=token,
        expires_at=now + timedelta(hours=settings.session_expiration_hours),
    )


@router.post("/logout")
async def admin_logout(token: str, db: Session = Depends(get_db)):
    """
    Admin logout.
    """
    revoke_admin_session(hash_token(token), db)
    return {"message": "Logged out"}


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(token: str, db: Session = Depends(get_db), _=Depends(verify_admin_token)):
    """
    Get dashboard statistics.
    """
    now = get_current_timestamp_utc()

    total_clients = db.query(Client).count()
    active_licenses = db.query(License).filter(
        and_(License.is_active == True, License.expires_at > now)
    ).count()
    expired_licenses = db.query(License).filter(License.expires_at <= now).count()
    disabled_licenses = db.query(License).filter(License.is_active == False).count()
    total_devices = db.query(LicenseDevice).count()

    # Count recent logins (last 24h)
    yesterday = now - timedelta(hours=24)
    recent_logins = db.query(AuditLog).filter(
        and_(
            AuditLog.action == AuditAction.CLIENT_LOGIN,
            AuditLog.created_at > yesterday,
        )
    ).count()

    return DashboardStats(
        total_clients=total_clients,
        active_licenses=active_licenses,
        expired_licenses=expired_licenses,
        disabled_licenses=disabled_licenses,
        total_devices=total_devices,
        recent_logins=recent_logins,
    )


@router.get("/clients", response_model=ClientListResponse)
async def list_clients(
    token: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str = Query(""),
    status: str = Query("all"),
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    List clients with pagination and filters.
    """
    query = db.query(Client)

    # Filter by status
    if status == "active":
        query = query.filter(Client.status == ClientStatus.ACTIVE)
    elif status == "inactive":
        query = query.filter(Client.status == ClientStatus.INACTIVE)

    # Search by login
    if search:
        query = query.filter(Client.login.ilike(f"%{search}%"))

    total = query.count()
    clients = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    now = get_current_timestamp_utc()

    for client in clients:
        license_obj = db.query(License).filter(License.client_id == client.id).first()
        devices_count = db.query(LicenseDevice).filter(LicenseDevice.client_id == client.id).count()

        days_remaining = None
        if license_obj:
            # Ensure both datetimes are timezone-aware
            expires_at = license_obj.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            days_remaining = (expires_at - now).days if expires_at > now else -1

        items.append(ClientResponse(
            id=client.id,
            login=client.login,
            status=client.status,
            created_at=client.created_at,
            last_login_at=client.last_login_at,
            devices_count=devices_count,
            license_expires_at=license_obj.expires_at if license_obj else None,
            days_until_expiry=days_remaining,
        ))

    return ClientListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Create new client and license.
    """
    ip_address = get_client_ip(request)

    # Check if login already exists
    existing = db.query(Client).filter(Client.login == client_data.login).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Login already exists")

    # Create client
    client = Client(
        login=client_data.login,
        password_hash=hash_password(client_data.password),
        status=ClientStatus.ACTIVE,
    )
    db.add(client)
    db.flush()

    # Get or create product
    product = db.query(Product).filter(Product.name == "survival_macro").first()
    if not product:
        product = Product(name="survival_macro", description="Survival Macro - Access Control")
        db.add(product)
        db.flush()

    # Create license
    now = get_current_timestamp_utc()
    expires_at = now + timedelta(days=client_data.license_days)

    license_obj = License(
        client_id=client.id,
        product_id=product.id,
        license_type=LicenseType.PREMIUM,
        device_limit=client_data.device_limit,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(license_obj)
    db.commit()

    # Audit log
    record_audit_log(
        db, AuditAction.CLIENT_CREATED,
        client_id=client.id,
        resource_type="client",
        resource_id=str(client.id),
        details=f"Login: {client.login}, Limit: {client_data.device_limit}, Days: {client_data.license_days}",
        ip_address=ip_address,
        success=True,
    )

    return ClientResponse(
        id=client.id,
        login=client.login,
        status=client.status,
        created_at=client.created_at,
        last_login_at=client.last_login_at,
    )


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    token: str,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Get client details.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    license_obj = db.query(License).filter(License.client_id == client.id).first()
    devices_count = db.query(LicenseDevice).filter(LicenseDevice.client_id == client.id).count()

    days_remaining = None
    if license_obj:
        now = get_current_timestamp_utc()
        days_remaining = (license_obj.expires_at - now).days if license_obj.expires_at > now else -1

    return ClientResponse(
        id=client.id,
        login=client.login,
        status=client.status,
        created_at=client.created_at,
        last_login_at=client.last_login_at,
        devices_count=devices_count,
        license_expires_at=license_obj.expires_at if license_obj else None,
        days_until_expiry=days_remaining,
    )


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    update_data: ClientUpdate,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Update client.
    """
    ip_address = get_client_ip(request)

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if update_data.login and update_data.login != client.login:
        existing = db.query(Client).filter(Client.login == update_data.login).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Login already exists")
        client.login = update_data.login

    if update_data.status:
        client.status = update_data.status

    if update_data.device_limit:
        license_obj = db.query(License).filter(License.client_id == client.id).first()
        if license_obj:
            license_obj.device_limit = update_data.device_limit

    db.commit()

    record_audit_log(
        db, AuditAction.CLIENT_CREATED,
        client_id=client.id,
        resource_type="client",
        resource_id=str(client.id),
        details=f"Updated: {update_data}",
        ip_address=ip_address,
        success=True,
    )

    return ClientResponse(
        id=client.id,
        login=client.login,
        status=client.status,
        created_at=client.created_at,
        last_login_at=client.last_login_at,
    )


@router.post("/clients/{client_id}/reset-password")
async def reset_client_password(
    client_id: int,
    new_password: str,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Reset client password.
    """
    ip_address = get_client_ip(request)

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    client.password_hash = hash_password(new_password)
    db.commit()

    record_audit_log(
        db, AuditAction.PASSWORD_CHANGED,
        client_id=client.id,
        resource_type="client",
        resource_id=str(client.id),
        ip_address=ip_address,
        success=True,
    )

    return {"message": "Password reset"}


@router.post("/clients/{client_id}/revoke-sessions")
async def revoke_client_sessions(
    client_id: int,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Revoke all client sessions.
    """
    ip_address = get_client_ip(request)

    from app.models import ClientSession
    sessions = db.query(ClientSession).filter(ClientSession.client_id == client_id).all()

    for session in sessions:
        session.is_revoked = True

    db.commit()

    record_audit_log(
        db, AuditAction.SESSION_REVOKED,
        client_id=client_id,
        resource_type="client",
        resource_id=str(client_id),
        details=f"Revoked {len(sessions)} sessions",
        ip_address=ip_address,
        success=True,
    )

    return {"message": "Sessions revoked", "count": len(sessions)}


@router.post("/clients/{client_id}/renew-license")
async def renew_license(
    client_id: int,
    days: int,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Renew client license.
    """
    ip_address = get_client_ip(request)

    license_obj = db.query(License).filter(License.client_id == client_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

    now = get_current_timestamp_utc()
    license_obj.expires_at = now + timedelta(days=days)
    license_obj.renewed_at = now
    db.commit()

    record_audit_log(
        db, AuditAction.LICENSE_RENEWED,
        client_id=client_id,
        resource_type="license",
        resource_id=str(license_obj.id),
        details=f"Renewed for {days} days",
        ip_address=ip_address,
        success=True,
    )

    return {"message": "License renewed", "expires_at": license_obj.expires_at}


@router.post("/clients/{client_id}/activate")
async def activate_client(
    client_id: int,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Activate client account.
    """
    ip_address = get_client_ip(request)

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    client.status = ClientStatus.ACTIVE
    db.commit()

    record_audit_log(
        db, AuditAction.LICENSE_ACTIVATED,
        client_id=client.id,
        resource_type="client",
        resource_id=str(client.id),
        ip_address=ip_address,
        success=True,
    )

    return {"message": "Client activated"}


@router.post("/clients/{client_id}/deactivate")
async def deactivate_client(
    client_id: int,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Deactivate client account.
    """
    ip_address = get_client_ip(request)

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    client.status = ClientStatus.INACTIVE
    db.commit()

    record_audit_log(
        db, AuditAction.LICENSE_DEACTIVATED,
        client_id=client.id,
        resource_type="client",
        resource_id=str(client.id),
        ip_address=ip_address,
        success=True,
    )

    return {"message": "Client deactivated"}


@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: int,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Delete client permanently.
    """
    ip_address = get_client_ip(request)

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    login = client.login
    db.delete(client)
    db.commit()

    record_audit_log(
        db, AuditAction.CLIENT_DELETED,
        resource_type="client",
        resource_id=str(client_id),
        details=f"Login: {login}",
        ip_address=ip_address,
        success=True,
    )

    return {"message": "Client deleted"}


@router.get("/clients/{client_id}/devices", response_model=list)
async def get_client_devices(
    client_id: int,
    token: str,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Get devices linked to client.
    """
    devices = db.query(LicenseDevice).filter(LicenseDevice.client_id == client_id).all()
    return [
        DeviceResponse(
            id=d.id,
            device_hash=d.device_hash,
            device_name=d.device_name,
            last_ip=d.last_ip,
            last_seen_at=d.last_seen_at,
            linked_at=d.linked_at,
        )
        for d in devices
    ]


@router.delete("/clients/{client_id}/devices/{device_id}")
async def remove_device(
    client_id: int,
    device_id: int,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_admin_token),
):
    """
    Remove device from client.
    """
    ip_address = get_client_ip(request)

    device = db.query(LicenseDevice).filter(
        and_(LicenseDevice.id == device_id, LicenseDevice.client_id == client_id)
    ).first()

    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    db.delete(device)
    db.commit()

    record_audit_log(
        db, AuditAction.DEVICE_REMOVED,
        client_id=client_id,
        resource_type="device",
        resource_id=str(device_id),
        ip_address=ip_address,
        success=True,
    )

    return {"message": "Device removed"}
