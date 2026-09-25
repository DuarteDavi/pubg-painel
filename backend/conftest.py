"""
pytest configuration with isolated test database and fixtures.
Ensures test independence: no state pollution, no rate limiter contamination.
"""

import pytest
import os
import sys

# Configure test environment BEFORE importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-only-for-testing-1234567890"
os.environ["ADMIN_LOGIN"] = "test_admin"
os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$o.xE88Cx3isFOC./SN6/fOJWHAhFzNkq0iGxVbqYMniO7gJJSa7GO"
os.environ["JWT_EXPIRATION_MINUTES"] = "15"
os.environ["JWT_REFRESH_EXPIRATION_DAYS"] = "7"
os.environ["RATE_LIMIT_ATTEMPTS"] = "5"
os.environ["RATE_LIMIT_MINUTES"] = "15"
os.environ["SESSION_EXPIRATION_HOURS"] = "8"
os.environ["DEBUG"] = "false"

# PostgreSQL test database - configured from environment or default
# Only set if not already configured
if not os.getenv("TEST_DATABASE_URL"):
    # Try to connect to WSL PostgreSQL
    os.environ["TEST_DATABASE_URL"] = "postgresql://postgres@127.0.0.1/test_db_concurrency"

# Clear any cached modules to ensure test config is used
for mod in list(sys.modules.keys()):
    if mod.startswith('app.'):
        del sys.modules[mod]

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import app components after env vars are set
from app.database import Base, get_db
from app.models import Product, AdminSession
from app.auth import hash_token, create_access_token
from app.utils import login_attempts
from app.config import settings


@pytest.fixture(scope="function")
def test_engine():
    """Create isolated in-memory SQLite database for each test"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def reset_rate_limiter():
    """Clear rate limiter state before and after test"""
    login_attempts.clear()
    yield
    login_attempts.clear()


@pytest.fixture(scope="function")
def test_app(test_db_session, reset_rate_limiter):
    """Create FastAPI app with isolated test database"""
    from main import app as main_app

    # Override get_db dependency to use test database
    async def override_get_db():
        yield test_db_session

    main_app.dependency_overrides[get_db] = override_get_db

    yield main_app

    # Cleanup
    main_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client(test_app):
    """Create TestClient for API testing"""
    return TestClient(test_app)


@pytest.fixture(scope="function")
def db(test_db_session):
    """Direct database session access for tests"""
    yield test_db_session


@pytest.fixture(scope="function")
def setup_test_data(test_db_session, test_app):
    """Setup initial test data"""
    # Create product (required by endpoints)
    product = Product(
        name="survival_macro",
        description="Test Product"
    )
    test_db_session.add(product)
    test_db_session.commit()

    yield test_db_session


@pytest.fixture(scope="function")
def setup_dual_products(test_db_session):
    """Setup both products for dual-product tests"""
    products = [
        Product(name="survival_macro", description="Spray Control - Survival Macro Access Control"),
        Product(name="survival_vision", description="Vision - Survival Vision Access Control"),
    ]
    for product in products:
        test_db_session.add(product)
    test_db_session.commit()

    yield test_db_session


@pytest.fixture(scope="function")
def admin_token(test_client):
    """Get valid admin authentication token via login"""
    response = test_client.post(
        "/api/admin/login",
        json={"login": "test_admin", "password": "test_password"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "sqlite: mark test as SQLite-compatible"
    )
    config.addinivalue_line(
        "markers", "postgres: mark test as requiring PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "antifraude: mark test as antifraude validation"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "rate_limit: mark test for rate limiting"
    )
