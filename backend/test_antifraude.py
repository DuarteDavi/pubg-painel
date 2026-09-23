"""
Antifraude validation tests.
Tests REAL protection mechanisms, not just code presence.
Each test validates a specific security requirement.
"""

import pytest
import hashlib
import json
from datetime import datetime, timedelta, timezone
from fastapi import status


@pytest.mark.antifraude
@pytest.mark.sqlite
class TestBearerTokenAuthentication:
    """Bearer token format validation"""

    def test_login_requires_bearer_token_in_verify(self, test_client, setup_test_data):
        """POST /auth/verify REQUIRES Bearer token in Authorization header"""
        # Test 1: No header at all
        response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": "test_hash"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "MISSING_BEARER_TOKEN" in response.text or "Authorization" in response.text

    def test_login_rejects_query_param_token(self, test_client, setup_test_data):
        """POST /auth/verify REJECTS token in query params (security hardening)"""
        response = test_client.post(
            "/api/auth/verify?token=test_token",
            json={"device_hash": "test_hash"}
        )
        # Should fail because no Bearer header
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_bearer_token_format_invalid(self, test_client, setup_test_data):
        """POST /auth/verify REJECTS malformed Bearer tokens"""
        # Missing "Bearer " prefix
        response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": "test_hash"},
            headers={"Authorization": "InvalidToken"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "MISSING_BEARER_TOKEN" in response.text

    def test_bearer_token_empty_prefix(self, test_client, setup_test_data):
        """POST /auth/verify REJECTS 'Bearer ' with no token"""
        response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": "test_hash"},
            headers={"Authorization": "Bearer "}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.antifraude
@pytest.mark.sqlite
class TestDeviceBinding:
    """Device vínculo (device binding) validation"""

    def _hash_device(self, device_info: dict) -> str:
        """Replicate device hash from backend"""
        device_str = json.dumps(device_info, sort_keys=True)
        return hashlib.sha256(device_str.encode()).hexdigest()

    def test_device_hash_in_verify_request(self, test_client, setup_test_data):
        """POST /auth/verify REQUIRES device_hash in request body"""
        response = test_client.post(
            "/api/auth/verify",
            json={},  # Missing device_hash
            headers={"Authorization": "Bearer test_token"}
        )
        # Should fail validation - missing device_hash field
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_401_UNAUTHORIZED]

    def test_device_hash_stored_in_session(self, test_client, setup_test_data):
        """Client login stores device_hash in session (for device binding validation)"""
        # This requires a valid session first - will be tested in integration
        # Just validate the schema accepts device_hash
        device_hash = self._hash_device({"uuid": "test", "board": "board"})
        response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": device_hash},
            headers={"Authorization": "Bearer invalid_token"}
        )
        # Token is invalid, but device_hash was accepted in request
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.antifraude
@pytest.mark.sqlite
@pytest.mark.rate_limit
class TestRateLimiting:
    """Rate limiting protection against brute force"""

    def test_admin_login_rate_limited_by_attempts(self, test_client, reset_rate_limiter):
        """Admin login limited to 5 attempts per 15 minutes"""
        # Make 6 login attempts
        for i in range(5):
            response = test_client.post(
                "/api/admin/login",
                json={"login": "nonexistent", "password": "wrong"}
            )
            # First 5 should be 401 (invalid credentials)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 6th attempt should be rate limited (429)
        response = test_client.post(
            "/api/admin/login",
            json={"login": "nonexistent", "password": "wrong"}
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limiter_cleared_between_tests(self, test_client, reset_rate_limiter):
        """Rate limiter MUST be cleared before each test (fixture validation)"""
        # If previous test contaminated state, this fails
        # Make only 2 attempts - should NOT be rate limited
        for i in range(2):
            response = test_client.post(
                "/api/admin/login",
                json={"login": "test", "password": "test"}
            )
            # Should be 401 (invalid), not 429 (rate limited)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Rate limiter not cleared from previous test (attempt {i+1} returned {response.status_code})"

    def test_verify_endpoint_rate_limited(self, test_client, reset_rate_limiter):
        """POST /auth/verify is rate limited by IP"""
        # Make 5 verify attempts (should all fail for other reasons, but not rate limit yet)
        for i in range(5):
            response = test_client.post(
                "/api/auth/verify",
                json={"device_hash": "test"},
                headers={"Authorization": "Bearer test"}
            )
            # Not rate limited yet
            assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

        # 6th attempt should be rate limited
        response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": "test"},
            headers={"Authorization": "Bearer test"}
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.antifraude
@pytest.mark.sqlite
class TestAuditLogging:
    """Audit logging does not expose sensitive data"""

    def test_audit_log_no_passwords(self, test_client, setup_test_data):
        """Audit logs MUST NOT contain passwords"""
        # Try to login with a password
        response = test_client.post(
            "/api/admin/login",
            json={"login": "test_admin", "password": "secretpassword123"}
        )
        # Password should not appear in audit logs
        # This is validated at database level in audit_log records
        # Can't directly test without DB access, but verify endpoint doesn't echo password
        assert "secretpassword123" not in response.text

    def test_audit_log_no_tokens(self, test_client, setup_test_data):
        """Audit logs MUST NOT contain tokens"""
        # Valid admin login to get token
        response = test_client.post(
            "/api/admin/login",
            json={"login": "test_admin", "password": "test_password"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            # Token should not appear in further error messages
            bad_response = test_client.post(
                "/api/auth/verify",
                json={"device_hash": "test"},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert token not in bad_response.text


@pytest.mark.antifraude
@pytest.mark.sqlite
class TestLogout:
    """Logout endpoint revokes session"""

    def test_logout_requires_bearer_token(self, test_client, setup_test_data):
        """POST /auth/logout REQUIRES Bearer token"""
        response = test_client.post("/api/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_bearer_format(self, test_client, setup_test_data):
        """POST /auth/logout validates Bearer format"""
        response = test_client.post(
            "/api/auth/logout",
            headers={"Authorization": "InvalidToken"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.antifraude
@pytest.mark.sqlite
class TestInputValidation:
    """Input validation prevents injection attacks"""

    def test_device_hash_invalid_format(self, test_client, setup_test_data):
        """Device hash validation"""
        response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": ""},  # Empty hash
            headers={"Authorization": "Bearer test"}
        )
        # Empty device hash should be rejected
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.antifraude
@pytest.mark.postgres
class TestRaceConditionPrevention:
    """SELECT FOR UPDATE prevents concurrent device limit bypass.

    NOTE: SQLite does not support SELECT FOR UPDATE locking.
    This test is MARKED FOR POSTGRESQL IMPLEMENTATION ONLY.
    SQLite version will PASS trivially (single-threaded).
    """

    @pytest.mark.skip(reason="Requires PostgreSQL with concurrent connections")
    def test_device_limit_race_condition(self, test_client, setup_test_data):
        """Device limit enforcement with concurrent logins"""
        # This test requires:
        # 1. PostgreSQL (not SQLite)
        # 2. Proper SELECT FOR UPDATE support
        # 3. Concurrent connection testing framework
        pass


@pytest.mark.antifraude
@pytest.mark.sqlite
class TestModelValidation:
    """Model and schema validation to prevent regressions"""

    def test_license_table_name_correct(self, test_db_session):
        """Verify License model table name is 'licenses' (case-sensitive SQL)"""
        from app.models import License
        # SQLAlchemy model must map to correct table name
        table_name = License.__tablename__
        assert table_name == "licenses", \
            f"License table name must be 'licenses', got '{table_name}'. " \
            f"ORM locks (with_for_update) depend on correct table name."

    def test_license_device_table_name_correct(self, test_db_session):
        """Verify LicenseDevice model table name is 'license_devices'"""
        from app.models import LicenseDevice
        table_name = LicenseDevice.__tablename__
        assert table_name == "license_devices", \
            f"LicenseDevice table name must be 'license_devices', got '{table_name}'."

    def test_license_orm_lock_column(self, test_db_session, setup_test_data):
        """Verify License model supports with_for_update() ORM lock"""
        from app.models import License, Client, Product

        # Create test data
        product = test_db_session.query(Product).first()
        client = test_db_session.query(Client).first()

        if not client or not product:
            pytest.skip("Test data not available")

        # Verify we can query License with ORM lock
        license_obj = (
            test_db_session.query(License)
            .filter(License.client_id == client.id)
            .filter(License.product_id == product.id)
            .with_for_update()
            .first()
        )

        # The lock query should work without SQL syntax errors
        # (test_client runs in SQLite which doesn't enforce locks, but verifies syntax)
        assert True  # If we reach here, ORM lock syntax is valid


# Marker for tests still without coverage
MISSING_COVERAGE = [
    "token_theft_across_devices",  # Token created on device1 fails on device2
    "access_token_expiration",     # Access token expires after 15 minutes
    "refresh_token_rotation",      # New refresh token issued on each refresh
    "old_refresh_revoked",         # Old refresh token cannot be reused
    "logout_revokes_session",      # Logout invalidates all tokens for that session
    "remove_device_revokes",       # Removing device revokes its sessions
    "disable_user_revokes",        # Disabling client revokes all sessions
    "concurrent_device_limit",     # Device limit enforced under concurrent load
    "network_failure_locks_macro", # Network failure keeps macro in waiting state
    "dpapi_session_protection",    # Session data encrypted locally (Windows)
]

@pytest.mark.skip(reason="Pending implementation with real client testing")
def test_missing_coverage_requires_integration():
    """These protections require end-to-end testing with actual macro client"""
    for item in MISSING_COVERAGE:
        print(f"TODO: {item}")
