from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from app.models import LicenseType, ClientStatus, AuditAction


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClientBase(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    status: ClientStatus = ClientStatus.ACTIVE


class ClientCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    product: str = Field(default="survival_macro")
    device_limit: int = Field(default=1, ge=1, le=10)
    license_days: int = Field(default=30, ge=1, le=365)

    @field_validator("login")
    @classmethod
    def validate_login(cls, v):
        if not v.isalnum():
            raise ValueError("Login must contain only alphanumeric characters")
        return v

    @field_validator("product")
    @classmethod
    def validate_product(cls, v):
        if v not in ("survival_macro", "survival_vision"):
            raise ValueError("Product must be 'survival_macro' or 'survival_vision'")
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class ClientUpdate(BaseModel):
    login: Optional[str] = Field(None, min_length=3, max_length=50)
    device_limit: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[ClientStatus] = None


class ClientResponse(ClientBase):
    id: int
    created_at: datetime
    last_login_at: Optional[datetime] = None
    devices_count: Optional[int] = None
    license_expires_at: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    product: Optional[str] = None

    class Config:
        from_attributes = True


class LicenseResponse(BaseModel):
    id: int
    license_type: LicenseType
    device_limit: int
    expires_at: datetime
    is_active: bool
    created_at: datetime
    renewed_at: Optional[datetime] = None
    devices_count: Optional[int] = None

    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    id: int
    device_hash: str
    device_name: Optional[str] = None
    last_ip: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    linked_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)
    product: str = Field(default="survival_macro")
    device: Optional[dict] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    login: str
    expires_at: datetime
    license_expires_at: datetime
    device_id: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class VerifyRequest(BaseModel):
    device_hash: dict | str

    @field_validator("device_hash", mode="before")
    @classmethod
    def validate_device_hash(cls, v):
        if isinstance(v, str):
            if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
                raise ValueError("Device hash must be valid SHA-256 hexadecimal (64 chars)")
        elif isinstance(v, dict):
            expected_keys = {
                "system_uuid_hash",
                "baseboard_serial_hash",
                "machine_guid_hash",
                "install_id_hash",
                "disk_serial_hash",
            }
            if set(v.keys()) != expected_keys:
                raise ValueError(
                    f"Device hash dict must contain exactly these keys: {expected_keys}"
                )
            non_empty_count = 0
            for key, val in v.items():
                if not isinstance(val, str):
                    raise ValueError(f"Device hash {key} must be string")
                if val:
                    if len(val) != 64 or not all(c in "0123456789abcdef" for c in val.lower()):
                        raise ValueError(f"Device hash {key} must be empty or valid SHA-256 hexadecimal")
                    non_empty_count += 1
            if non_empty_count < 2:
                raise ValueError("At least two device hash components are required")
        else:
            raise ValueError("Device hash must be string or dict")
        return v


class VerifyResponse(BaseModel):
    valid: bool
    login: str
    expires_at: datetime
    license_expires_at: datetime
    device_id: str


class AdminLoginRequest(BaseModel):
    login: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuditLogResponse(BaseModel):
    id: int
    action: AuditAction
    admin_id: Optional[int] = None
    client_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_clients: int
    active_licenses: int
    expired_licenses: int
    disabled_licenses: int
    total_devices: int
    recent_logins: int


class ClientListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ClientResponse]


class RefreshTokenRequest(BaseModel):
    refresh_token: str
