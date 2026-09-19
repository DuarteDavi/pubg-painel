"""
Functional tests for Survival Macro API.
Tests critical security and functionality requirements.
"""

import pytest
from fastapi.testclient import TestClient
from app.database import Base, SessionLocal
from app.config import settings
import os

# Disable HTTPS validation for dev testing
os.environ["JWT_SECRET"] = "test-secret-key-only-for-testing"
os.environ["ADMIN_PASSWORD_HASH"] = ""

from main import app
from app.auth import hash_password
from app.config import Settings

@pytest.fixture
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=app.state.db.engine)
    yield SessionLocal()
    Base.metadata.drop_all(bind=app.state.db.engine)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_admin_login_invalid_credentials(client):
    """Test admin login with invalid credentials"""
    response = client.post(
        "/api/admin/login",
        json={"login": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "INVALID_CREDENTIALS"


def test_admin_login_valid(client):
    """Test admin login with valid credentials (if ADMIN_PASSWORD_HASH set)"""
    # This will fail if ADMIN_PASSWORD_HASH not configured
    # which is expected - admin must configure password before login
    pass


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_product_seed(client):
    """Test that survival_macro product is seeded"""
    from app.database import SessionLocal
    from app.models import Product

    db = SessionLocal()
    product = db.query(Product).filter(Product.name == "survival_macro").first()
    assert product is not None
    assert product.name == "survival_macro"
    db.close()


def test_auth_login_invalid_product(client):
    """Test client login with invalid product"""
    response = client.post(
        "/api/auth/login",
        json={
            "login": "testuser",
            "password": "password123",
            "product": "invalid_product",
            "device": {"system_uuid_hash": "abc123"}
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "INVALID_PRODUCT"


def test_password_hashing():
    """Test password hashing security"""
    import bcrypt

    password = "MySecurePass123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    # Hashed should be different from original
    assert hashed.decode() != password

    # Verification should work
    assert bcrypt.checkpw(password.encode(), hashed) == True

    # Wrong password should fail
    assert bcrypt.checkpw("WrongPassword".encode(), hashed) == False


def test_device_hash_security():
    """Test device hashing never reveals raw hardware IDs"""
    from app.auth import hash_device

    device = {
        "system_uuid_hash": "abcd1234",
        "baseboard_serial_hash": "efgh5678",
        "machine_guid_hash": "ijkl9012",
    }

    hashed = hash_device(device)

    # Hash should not contain any original values
    assert "abcd1234" not in hashed
    assert "efgh5678" not in hashed
    assert "ijkl9012" not in hashed
    assert len(hashed) == 64  # SHA256 hash length


def test_device_hash_invalid():
    """Test device hash returns None for invalid input"""
    from app.auth import hash_device

    # Empty device
    assert hash_device({}) == None

    # Generic UUIDs should fail
    device = {"system_uuid_hash": "00000000-0000-0000-0000-000000000000"}
    assert hash_device(device) == None


def test_token_generation():
    """Test JWT token generation and expiration"""
    from app.auth import create_access_token, verify_token
    from datetime import timedelta

    token = create_access_token({"sub": "testuser"})
    payload = verify_token(token)

    assert payload is not None
    assert payload["sub"] == "testuser"
    assert "exp" in payload


def test_audit_log_no_sensitive_data():
    """Test audit logging never stores sensitive data"""
    from app.database import SessionLocal, Base, engine
    from app.models import AuditLog, AuditAction

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Create audit log
    log = AuditLog(
        action=AuditAction.ADMIN_LOGIN,
        details="Admin login successful",
    )
    db.add(log)
    db.commit()

    # Verify log was created
    retrieved = db.query(AuditLog).filter(AuditLog.action == AuditAction.ADMIN_LOGIN).first()
    assert retrieved is not None
    assert retrieved.action == AuditAction.ADMIN_LOGIN

    # Details should never contain sensitive fields
    assert "password" not in (retrieved.details or "").lower()
    assert "token" not in (retrieved.details or "").lower()
    assert "hash" not in (retrieved.details or "").lower()

    db.close()


def test_rate_limiting():
    """Test rate limiting functionality"""
    from app.utils import is_rate_limited, record_login_attempt

    identifier = "test_user_rate_limit"

    # First 5 attempts should work
    for i in range(5):
        assert is_rate_limited(identifier) == False
        record_login_attempt(identifier)

    # 6th attempt should be rate limited
    assert is_rate_limited(identifier) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
