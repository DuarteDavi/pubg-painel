from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, LargeBinary, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import enum


class LicenseType(str, enum.Enum):
    TRIAL = "trial"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ClientStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    BLOCKED = "blocked"


class AuditAction(str, enum.Enum):
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGIN_FAILED = "admin_login_failed"
    CLIENT_LOGIN = "client_login"
    CLIENT_LOGIN_FAILED = "client_login_failed"
    CLIENT_CREATED = "client_created"
    CLIENT_DELETED = "client_deleted"
    LICENSE_RENEWED = "license_renewed"
    LICENSE_ACTIVATED = "license_activated"
    LICENSE_DEACTIVATED = "license_deactivated"
    DEVICE_LINKED = "device_linked"
    DEVICE_REMOVED = "device_removed"
    DEVICE_LIMIT_REACHED = "device_limit_reached"
    PASSWORD_CHANGED = "password_changed"
    SESSION_REVOKED = "session_revoked"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    licenses = relationship("License", back_populates="product")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    licenses = relationship("License", back_populates="client", cascade="all, delete-orphan")
    devices = relationship("LicenseDevice", back_populates="client", cascade="all, delete-orphan")
    sessions = relationship("ClientSession", back_populates="client", cascade="all, delete-orphan")


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    license_type = Column(Enum(LicenseType), default=LicenseType.TRIAL)
    device_limit = Column(Integer, default=1, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    renewed_at = Column(DateTime(timezone=True), nullable=True)

    client = relationship("Client", back_populates="licenses")
    product = relationship("Product", back_populates="licenses")
    devices = relationship("LicenseDevice", back_populates="license", cascade="all, delete-orphan")


class LicenseDevice(Base):
    __tablename__ = "license_devices"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    device_hash = Column(String(255), nullable=False, index=True)
    device_name = Column(String(100), nullable=True)
    last_ip = Column(String(45), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    linked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    license = relationship("License", back_populates="devices")
    client = relationship("Client", back_populates="devices")


class ClientSession(Base):
    __tablename__ = "client_sessions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    refresh_expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    device_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="sessions")


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String(45), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(Enum(AuditAction), nullable=False, index=True)
    admin_id = Column(Integer, nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    client = relationship("Client")
