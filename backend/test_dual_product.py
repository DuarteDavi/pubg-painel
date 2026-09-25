"""
Dual-product functional tests for Survival Macro and Survival Vision.
Tests real authentication flows, product isolation, and license validation.
"""

import pytest
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import status
from app.models import Product, Client, License, ClientStatus
from app.auth import hash_device


@pytest.mark.sqlite
class TestProductSeed:
    """Verify both products are seeded correctly"""

    def test_survival_macro_exists(self, setup_dual_products):
        """Verify survival_macro product exists"""
        db = setup_dual_products
        product = db.query(Product).filter(Product.name == "survival_macro").first()
        assert product is not None
        assert product.name == "survival_macro"

    def test_survival_vision_exists(self, setup_dual_products):
        """Verify survival_vision product exists"""
        db = setup_dual_products
        product = db.query(Product).filter(Product.name == "survival_vision").first()
        assert product is not None
        assert product.name == "survival_vision"


@pytest.mark.sqlite
class TestValidLoginFlows:
    """Test real login flows with valid credentials"""

    @pytest.fixture
    def macro_credentials(self, test_client, admin_token, setup_dual_products):
        """Create macro client and return credentials"""
        response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "macrologinvalid",
                "password": "MacroValidPass2026",
                "password_confirm": "MacroValidPass2026",
                "product": "survival_macro",
                "device_limit": 2,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        return {
            "login": "macrologinvalid",
            "password": "MacroValidPass2026",
            "product": "survival_macro",
        }

    @pytest.fixture
    def vision_credentials(self, test_client, admin_token, setup_dual_products):
        """Create vision client and return credentials"""
        response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "visionloginvalid",
                "password": "VisionValidPass2026",
                "password_confirm": "VisionValidPass2026",
                "product": "survival_vision",
                "device_limit": 2,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        return {
            "login": "visionloginvalid",
            "password": "VisionValidPass2026",
            "product": "survival_vision",
        }

    @pytest.fixture
    def valid_device_info(self):
        """Device info matching schema requirements"""
        return {
            "system_uuid_hash": "test_system_uuid_12345678901234567890",
            "baseboard_serial_hash": "test_baseboard_serial_1234567890",
            "machine_guid_hash": "test_machine_guid_1234567890123456",
            "install_id_hash": "test_install_id_1234567890123456",
            "disk_serial_hash": "test_disk_serial_1234567890123456",
        }

    def test_login_macro_valid_returns_tokens(self, test_client, macro_credentials, valid_device_info):
        """Login with valid macro credentials returns access and refresh tokens"""
        response = test_client.post(
            "/api/auth/login",
            json={
                "login": macro_credentials["login"],
                "password": macro_credentials["password"],
                "product": macro_credentials["product"],
                "device": valid_device_info,
            },
        )
        assert response.status_code == status.HTTP_200_OK, f"Expected 200 but got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["login"] == macro_credentials["login"]
        assert "expires_at" in data
        assert "device_id" in data
        return data

    def test_login_vision_valid_returns_tokens(self, test_client, vision_credentials, valid_device_info):
        """Login with valid vision credentials returns access and refresh tokens"""
        response = test_client.post(
            "/api/auth/login",
            json={
                "login": vision_credentials["login"],
                "password": vision_credentials["password"],
                "product": vision_credentials["product"],
                "device": valid_device_info,
            },
        )
        assert response.status_code == status.HTTP_200_OK, f"Expected 200 but got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["login"] == vision_credentials["login"]
        return data


@pytest.mark.sqlite
class TestProductIsolation:
    """Test that credentials are isolated by product"""

    @pytest.fixture
    def macro_client_vision_product(self, test_client, admin_token, setup_dual_products):
        """Create macro client, try login with vision product"""
        response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "macroclientisolation",
                "password": "MacroIsolationPass2026",
                "password_confirm": "MacroIsolationPass2026",
                "product": "survival_macro",
                "device_limit": 1,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        return {
            "login": "macroclientisolation",
            "password": "MacroIsolationPass2026",
            "product": "survival_macro",
        }

    @pytest.fixture
    def vision_client_macro_product(self, test_client, admin_token, setup_dual_products):
        """Create vision client, try login with macro product"""
        response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "visionclientisolation",
                "password": "VisionIsolationPass2026",
                "password_confirm": "VisionIsolationPass2026",
                "product": "survival_vision",
                "device_limit": 1,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        return {
            "login": "visionclientisolation",
            "password": "VisionIsolationPass2026",
            "product": "survival_vision",
        }

    @pytest.fixture
    def valid_device_info(self):
        """Device info matching schema requirements"""
        return {
            "system_uuid_hash": "test_isolation_uuid_12345678901234",
            "baseboard_serial_hash": "test_isolation_board_1234567890",
            "machine_guid_hash": "test_isolation_guid_1234567890123",
            "install_id_hash": "test_isolation_install_1234567890",
            "disk_serial_hash": "test_isolation_disk_1234567890123",
        }

    def test_macro_client_rejected_with_vision_product(self, test_client, macro_client_vision_product, valid_device_info):
        """Macro client cannot login with survival_vision product"""
        response = test_client.post(
            "/api/auth/login",
            json={
                "login": macro_client_vision_product["login"],
                "password": macro_client_vision_product["password"],
                "product": "survival_vision",
                "device": valid_device_info,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "LICENSE_DISABLED" in response.text

    def test_vision_client_rejected_with_macro_product(self, test_client, vision_client_macro_product, valid_device_info):
        """Vision client cannot login with survival_macro product"""
        response = test_client.post(
            "/api/auth/login",
            json={
                "login": vision_client_macro_product["login"],
                "password": vision_client_macro_product["password"],
                "product": "survival_macro",
                "device": valid_device_info,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "LICENSE_DISABLED" in response.text


@pytest.mark.sqlite
class TestCompleteAuthFlows:
    """Test complete authentication flows: login → verify → logout"""

    @pytest.fixture
    def vision_login_token(self, test_client, admin_token, setup_dual_products):
        """Setup vision client and login"""
        # Create client
        create_response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "visionflowtest",
                "password": "VisionFlowPass2026",
                "password_confirm": "VisionFlowPass2026",
                "product": "survival_vision",
                "device_limit": 1,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Login - use valid SHA256 hashes
        device_info = {
            "system_uuid_hash": hashlib.sha256(b"vision_flow_uuid").hexdigest(),
            "baseboard_serial_hash": hashlib.sha256(b"vision_flow_board").hexdigest(),
            "machine_guid_hash": hashlib.sha256(b"vision_flow_guid").hexdigest(),
            "install_id_hash": hashlib.sha256(b"vision_flow_install").hexdigest(),
            "disk_serial_hash": hashlib.sha256(b"vision_flow_disk").hexdigest(),
        }
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "login": "visionflowtest",
                "password": "VisionFlowPass2026",
                "product": "survival_vision",
                "device": device_info,
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        return {
            "access_token": login_response.json()["access_token"],
            "device_hash": device_info,  # Vision sends DICT with 5 hashes
        }

    @pytest.fixture
    def macro_login_token(self, test_client, admin_token, setup_dual_products):
        """Setup macro client and login"""
        # Create client
        create_response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "macroflowtest",
                "password": "MacroFlowPass2026",
                "password_confirm": "MacroFlowPass2026",
                "product": "survival_macro",
                "device_limit": 1,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Login - Macro sends only machine_guid_hash (not all 5 components)
        machine_guid = hashlib.sha256(b"macro_flow_guid").hexdigest()
        device_info = {
            "machine_guid_hash": machine_guid,
            "device_name": "DESKTOP-MACRO",
        }
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "login": "macroflowtest",
                "password": "MacroFlowPass2026",
                "product": "survival_macro",
                "device": device_info,
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        return {
            "access_token": login_response.json()["access_token"],
            "device_hash": machine_guid,  # Macro sends only the machine_guid_hash STRING in verify
        }

    def test_vision_verify_logout_flow(self, test_client, vision_login_token):
        """Vision: login → verify → logout → verify fails"""
        token = vision_login_token["access_token"]
        device_hash = vision_login_token["device_hash"]

        # Verify with valid token
        verify_response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": device_hash},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert verify_response.status_code == status.HTTP_200_OK
        verify_data = verify_response.json()
        assert verify_data["valid"] is True

        # Logout
        logout_response = test_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == status.HTTP_200_OK

        # Verify after logout should fail
        verify_after_logout = test_client.post(
            "/api/auth/verify",
            json={"device_hash": device_hash},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert verify_after_logout.status_code == status.HTTP_401_UNAUTHORIZED
        assert "SESSION_REVOKED" in verify_after_logout.text

    def test_macro_verify_logout_flow(self, test_client, macro_login_token):
        """Macro: login → verify → logout → verify fails"""
        token = macro_login_token["access_token"]
        device_hash = macro_login_token["device_hash"]

        # Verify with valid token
        verify_response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": device_hash},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert verify_response.status_code == status.HTTP_200_OK
        verify_data = verify_response.json()
        assert verify_data["valid"] is True

        # Logout
        logout_response = test_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == status.HTTP_200_OK

        # Verify after logout should fail
        verify_after_logout = test_client.post(
            "/api/auth/verify",
            json={"device_hash": device_hash},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert verify_after_logout.status_code == status.HTTP_401_UNAUTHORIZED
        assert "SESSION_REVOKED" in verify_after_logout.text

    def test_vision_device_binding_mismatch(self, test_client, admin_token, setup_dual_products):
        """Vision: Different device_hash in verify is rejected"""
        # Create client
        create_response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "visiondevicemismatch",
                "password": "VisionDeviceMismatch2026",
                "password_confirm": "VisionDeviceMismatch2026",
                "product": "survival_vision",
                "device_limit": 1,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Login with device A
        device_a = {
            "system_uuid_hash": "device_a_uuid_1234567890123456789",
            "baseboard_serial_hash": "device_a_board_123456789012345",
            "machine_guid_hash": "device_a_guid_123456789012345678",
            "install_id_hash": "device_a_install_1234567890123456",
            "disk_serial_hash": "device_a_disk_123456789012345678",
        }
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "login": "visiondevicemismatch",
                "password": "VisionDeviceMismatch2026",
                "product": "survival_vision",
                "device": device_a,
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Try to verify with device B hash (different device)
        device_b = {
            "system_uuid_hash": "device_b_uuid_9876543210987654321",
            "baseboard_serial_hash": "device_b_board_987654321098765",
            "machine_guid_hash": "device_b_guid_987654321098765432",
            "install_id_hash": "device_b_install_9876543210987654",
            "disk_serial_hash": "device_b_disk_987654321098765432",
        }
        device_b_hash = hash_device(device_b)

        verify_response = test_client.post(
            "/api/auth/verify",
            json={"device_hash": device_b_hash},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert verify_response.status_code == status.HTTP_403_FORBIDDEN
        assert "DEVICE_MISMATCH" in verify_response.text


@pytest.mark.sqlite
class TestLicenseValidation:
    """Test license expiration and deactivation"""

    def test_vision_expired_license_rejected(self, test_client, admin_token, setup_dual_products, db):
        """Vision client with expired license is rejected"""
        db_session = db
        # Get vision product
        vision_product = db_session.query(Product).filter(Product.name == "survival_vision").first()

        # Create client via admin API
        create_response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "visionexpired",
                "password": "VisionExpiredPass2026",
                "password_confirm": "VisionExpiredPass2026",
                "product": "survival_vision",
                "device_limit": 1,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        client_id = create_response.json()["id"]

        # Manually expire the license
        license_obj = db_session.query(License).filter(
            License.client_id == client_id,
            License.product_id == vision_product.id,
        ).first()
        assert license_obj is not None
        license_obj.expires_at = datetime.now(tz=timezone.utc) - timedelta(days=1)
        db_session.commit()

        # Try to login with expired license
        device_info = {
            "system_uuid_hash": "expired_uuid_1234567890123456789",
            "baseboard_serial_hash": "expired_board_123456789012345",
            "machine_guid_hash": "expired_guid_123456789012345678",
            "install_id_hash": "expired_install_1234567890123456",
            "disk_serial_hash": "expired_disk_123456789012345678",
        }
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "login": "visionexpired",
                "password": "VisionExpiredPass2026",
                "product": "survival_vision",
                "device": device_info,
            },
        )
        assert login_response.status_code == status.HTTP_403_FORBIDDEN
        assert "LICENSE_EXPIRED" in login_response.text

    def test_vision_deactivated_license_rejected(self, test_client, admin_token, setup_dual_products, db):
        """Vision client with deactivated license is rejected"""
        db_session = db
        # Get vision product
        vision_product = db_session.query(Product).filter(Product.name == "survival_vision").first()

        # Create client
        create_response = test_client.post(
            "/api/admin/clients",
            json={
                "login": "visiondeactivated",
                "password": "VisionDeactivatedPass2026",
                "password_confirm": "VisionDeactivatedPass2026",
                "product": "survival_vision",
                "device_limit": 1,
                "license_days": 30,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        client_id = create_response.json()["id"]

        # Deactivate the license
        license_obj = db_session.query(License).filter(
            License.client_id == client_id,
            License.product_id == vision_product.id,
        ).first()
        assert license_obj is not None
        license_obj.is_active = False
        db_session.commit()

        # Try to login with deactivated license
        device_info = {
            "system_uuid_hash": "deactivated_uuid_1234567890123456",
            "baseboard_serial_hash": "deactivated_board_123456789012",
            "machine_guid_hash": "deactivated_guid_1234567890123",
            "install_id_hash": "deactivated_install_123456789012",
            "disk_serial_hash": "deactivated_disk_1234567890123",
        }
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "login": "visiondeactivated",
                "password": "VisionDeactivatedPass2026",
                "product": "survival_vision",
                "device": device_info,
            },
        )
        assert login_response.status_code == status.HTTP_403_FORBIDDEN
        assert "LICENSE_DISABLED" in login_response.text
