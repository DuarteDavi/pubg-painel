from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import AuditLog, AuditAction, AdminSession, ClientSession
from app.config import settings
from collections import defaultdict
import hashlib

login_attempts = defaultdict(list)


def record_audit_log(
    db: Session,
    action: AuditAction,
    admin_id: int = None,
    client_id: int = None,
    resource_type: str = None,
    resource_id: str = None,
    details: str = None,
    ip_address: str = None,
    success: bool = True,
):
    """
    Record action in audit log.
    Never logs passwords, full tokens, or sensitive data.
    """
    log = AuditLog(
        action=action,
        admin_id=admin_id,
        client_id=client_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        success=success,
    )
    db.add(log)
    try:
        db.commit()
    except Exception:
        db.rollback()


def is_rate_limited(identifier: str) -> bool:
    """
    Check if identifier has exceeded login attempts.
    Implements rate limiting: N attempts in M minutes.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=settings.rate_limit_minutes)

    login_attempts[identifier] = [
        ts for ts in login_attempts[identifier] if ts > cutoff
    ]

    if len(login_attempts[identifier]) >= settings.rate_limit_attempts:
        return True

    return False


def record_login_attempt(identifier: str):
    """
    Record a login attempt for rate limiting.
    """
    login_attempts[identifier].append(datetime.now(timezone.utc))


def verify_admin_session(token_hash: str, db: Session) -> bool:
    """
    Verify if admin session is valid and not revoked.
    """
    session = db.query(AdminSession).filter(
        AdminSession.token_hash == token_hash,
        AdminSession.is_revoked == False,
        AdminSession.expires_at > datetime.now(timezone.utc)
    ).first()
    return session is not None


def verify_client_session(token_hash: str, db: Session) -> dict:
    """
    Verify if client session is valid and return session data.
    """
    session = db.query(ClientSession).filter(
        ClientSession.token_hash == token_hash,
        ClientSession.is_revoked == False,
        ClientSession.expires_at > datetime.now(timezone.utc)
    ).first()

    if not session:
        return None

    return {
        "client_id": session.client_id,
        "device_hash": session.device_hash,
        "expires_at": session.expires_at,
    }


def revoke_client_session(token_hash: str, db: Session):
    """
    Revoke a client session.
    """
    session = db.query(ClientSession).filter(
        ClientSession.token_hash == token_hash
    ).first()

    if session:
        session.is_revoked = True
        db.commit()


def revoke_admin_session(token_hash: str, db: Session):
    """
    Revoke an admin session.
    """
    session = db.query(AdminSession).filter(
        AdminSession.token_hash == token_hash
    ).first()

    if session:
        session.is_revoked = True
        db.commit()


def normalize_device_hash(device_hash: str) -> str:
    """
    Normalize device hash to prevent tampering.
    """
    if not device_hash or len(device_hash) < 32:
        return None

    return hashlib.sha256(device_hash.encode()).hexdigest()


def get_client_ip(request) -> str:
    """
    Extract client IP from request headers.
    """
    if request.headers.get("x-forwarded-for"):
        return request.headers.get("x-forwarded-for").split(",")[0].strip()
    return request.client.host if request.client else "unknown"
