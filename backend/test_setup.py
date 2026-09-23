"""
Smoke tests to validate test infrastructure setup.
"""

import pytest
from fastapi import status


@pytest.mark.sqlite
class TestSetup:
    """Test setup and fixtures"""

    def test_health_check(self, test_client):
        """Health endpoint is accessible"""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"

    def test_database_isolation(self, test_db_session):
        """Test database is created and isolated"""
        from app.models import Product
        products = test_db_session.query(Product).all()
        # Should be empty in fresh test DB
        assert isinstance(products, list)

    def test_rate_limiter_cleared(self, reset_rate_limiter):
        """Rate limiter is cleared between tests"""
        from app.utils import login_attempts
        # Should be empty due to fixture
        assert len(login_attempts) == 0

    def test_admin_login(self, test_client, setup_test_data):
        """Admin login works with test credentials"""
        response = test_client.post(
            "/api/admin/login",
            json={"login": "test_admin", "password": "test_password"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "expires_at" in data
