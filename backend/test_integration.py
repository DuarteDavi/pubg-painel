"""
Integration tests for Survival Macro Admin Panel.
Tests real API workflows: login, CRUD operations, licenses, devices.
"""

import pytest
import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:3020"
API_PREFIX = f"{BASE_URL}/api"

# Credenciais de teste (configuradas via setup_admin.py)
ADMIN_LOGIN = "administrator"
ADMIN_PASSWORD = "SecurePass2026"

class TestAdminFlow:
    """Test admin panel workflows"""

    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{API_PREFIX}/admin/login",
            json={
                "login": ADMIN_LOGIN,
                "password": ADMIN_PASSWORD
            }
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]

    def test_01_admin_login(self):
        """Test admin login endpoint"""
        response = requests.post(
            f"{API_PREFIX}/admin/login",
            json={
                "login": ADMIN_LOGIN,
                "password": ADMIN_PASSWORD
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_02_admin_login_invalid(self):
        """Test admin login with invalid credentials"""
        response = requests.post(
            f"{API_PREFIX}/admin/login",
            json={
                "login": ADMIN_LOGIN,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "INVALID_CREDENTIALS" in response.text

    def _get_headers(self, token):
        """Helper to create Bearer token header"""
        return {"Authorization": f"Bearer {token}"}

    def test_03_dashboard_stats(self, admin_token):
        """Test dashboard statistics endpoint"""
        response = requests.get(
            f"{API_PREFIX}/admin/dashboard",
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_clients" in data
        assert "active_licenses" in data
        assert "expired_licenses" in data

    def test_04_create_client(self, admin_token):
        """Test creating a new client"""
        response = requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "testclient001",
                "password": "TestPass@2026",
                "password_confirm": "TestPass@2026",
                "device_limit": 2,
                "license_days": 30
            },
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["login"] == "testclient001"
        assert data["status"] == "active"

    def test_05_create_duplicate_client(self, admin_token):
        """Test that duplicate login is rejected"""
        # First client
        requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "duplicate_test",
                "password": "Pass@2026Test",
                "password_confirm": "Pass@2026Test",
                "device_limit": 1,
                "license_days": 30
            },
            headers=self._get_headers(admin_token)
        )

        # Try duplicate
        response = requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "duplicate_test",
                "password": "Pass@2026Test",
                "password_confirm": "Pass@2026Test",
                "device_limit": 1,
                "license_days": 30
            },
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 400

    def test_06_list_clients(self, admin_token):
        """Test listing clients with pagination"""
        response = requests.get(
            f"{API_PREFIX}/admin/clients",
            params={
                "page": 1,
                "page_size": 10
            },
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_07_get_client_detail(self, admin_token):
        """Test getting client details"""
        # Create a client first
        create_resp = requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "detail_test_client",
                "password": "Detail@Pass2026",
                "password_confirm": "Detail@Pass2026",
                "device_limit": 3,
                "license_days": 60
            },
            headers=self._get_headers(admin_token)
        )
        client_id = create_resp.json()["id"]

        # Get details
        response = requests.get(
            f"{API_PREFIX}/admin/clients/{client_id}",
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["login"] == "detail_test_client"

    def test_08_activate_deactivate_client(self, admin_token):
        """Test activating and deactivating client"""
        # Create client
        create_resp = requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "status_test_client",
                "password": "Status@Pass2026",
                "password_confirm": "Status@Pass2026",
                "device_limit": 1,
                "license_days": 30
            },
            headers=self._get_headers(admin_token)
        )
        client_id = create_resp.json()["id"]

        # Deactivate
        response = requests.post(
            f"{API_PREFIX}/admin/clients/{client_id}/deactivate",
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"

        # Activate
        response = requests.post(
            f"{API_PREFIX}/admin/clients/{client_id}/activate",
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_09_reset_password(self, admin_token):
        """Test resetting client password"""
        # Create client
        create_resp = requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "pwd_reset_client",
                "password": "Initial@Pass2026",
                "password_confirm": "Initial@Pass2026",
                "device_limit": 1,
                "license_days": 30
            },
            headers=self._get_headers(admin_token)
        )
        client_id = create_resp.json()["id"]

        # Reset password
        response = requests.post(
            f"{API_PREFIX}/admin/clients/{client_id}/reset-password",
            json={"new_password": "NewPass@2026"},
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200

    def test_10_renew_license(self, admin_token):
        """Test renewing client license"""
        # Create client with short license
        create_resp = requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "renew_test_client",
                "password": "Renew@Pass2026",
                "password_confirm": "Renew@Pass2026",
                "device_limit": 1,
                "license_days": 1
            },
            headers=self._get_headers(admin_token)
        )
        client_id = create_resp.json()["id"]

        # Renew license
        response = requests.post(
            f"{API_PREFIX}/admin/clients/{client_id}/renew-license",
            json={"days": 30},
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "license_expires_at" in data

    def test_11_device_operations(self, admin_token):
        """Test device management"""
        # Create client
        create_resp = requests.post(
            f"{API_PREFIX}/admin/clients",
            json={
                "login": "device_test_client",
                "password": "Device@Pass2026",
                "password_confirm": "Device@Pass2026",
                "device_limit": 3,
                "license_days": 30
            },
            headers=self._get_headers(admin_token)
        )
        client_id = create_resp.json()["id"]

        # List devices (should be empty)
        response = requests.get(
            f"{API_PREFIX}/admin/clients/{client_id}/devices",
            headers=self._get_headers(admin_token)
        )
        assert response.status_code == 200
        devices = response.json()
        assert isinstance(devices, list)

    def test_12_rate_limiting(self):
        """Test rate limiting on admin login"""
        attempts = 0
        for i in range(6):
            response = requests.post(
                f"{API_PREFIX}/admin/login",
                json={
                    "login": ADMIN_LOGIN,
                    "password": "wrong"
                }
            )
            if response.status_code == 401:
                attempts += 1
            elif response.status_code == 429:
                # Rate limited
                break

        assert attempts >= 5  # First 5 attempts return 401


class TestClientAuthFlow:
    """Test client authentication flow"""

    def test_client_login_valid_product(self):
        """Test client login with valid product"""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={
                "login": "testuser",
                "password": "password",
                "product": "survival_macro",
                "device": {
                    "system_uuid_hash": "abc123def456",
                    "baseboard_serial_hash": "serial789"
                }
            }
        )
        # Should fail with invalid credentials (client doesn't exist)
        # But product validation should pass
        if response.status_code != 200:
            assert response.status_code in [400, 401]

    def test_client_login_invalid_product(self):
        """Test client login with invalid product"""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={
                "login": "testuser",
                "password": "password",
                "product": "nonexistent_product",
                "device": {"system_uuid_hash": "abc123"}
            }
        )
        assert response.status_code == 400
        assert "INVALID_PRODUCT" in response.text

    def test_generic_uuid_rejected(self):
        """Test that generic UUIDs are rejected"""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={
                "login": "anyuser",
                "password": "anypass",
                "product": "survival_macro",
                "device": {
                    "system_uuid_hash": "00000000-0000-0000-0000-000000000000"
                }
            }
        )
        # Should be rejected or treated as invalid device
        assert response.status_code in [400, 401]


class TestHealthAndBasic:
    """Basic health checks"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_product_exists(self):
        """Test that survival_macro product exists"""
        response = requests.post(
            f"{API_PREFIX}/auth/login",
            json={
                "login": "test",
                "password": "test",
                "product": "survival_macro",
                "device": {"system_uuid_hash": "test123"}
            }
        )
        # Should not return INVALID_PRODUCT
        assert response.status_code != 400 or "INVALID_PRODUCT" not in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
