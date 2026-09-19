import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import hashlib
from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_device(device_info: dict) -> str:
    device_string = "".join([
        device_info.get("system_uuid_hash", ""),
        device_info.get("baseboard_serial_hash", ""),
        device_info.get("machine_guid_hash", ""),
        device_info.get("install_id_hash", ""),
        device_info.get("disk_serial_hash", ""),
    ]).strip()

    if not device_string:
        return None

    # Reject generic UUIDs (all zeros/hyphens, all Fs/hyphens, etc.)
    cleaned = device_string.replace("-", "").replace("0", "").replace("f", "").replace("F", "")
    if not cleaned or len(cleaned) < 5:
        return None

    return hashlib.sha256(device_string.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expiration_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def verify_admin_password(password: str) -> bool:
    if not settings.admin_password_hash:
        return False
    return verify_password(password, settings.admin_password_hash)


def get_current_timestamp_utc() -> datetime:
    return datetime.now(timezone.utc)
