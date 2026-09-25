"""
Test real payloads from Macro Simple and Vision clients.
Reproduce exact login and verify flows as observed in production.
"""

import pytest
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestMacroSimplePayloads:
    """Macro Simple sends single machine_guid_hash string in both login and verify"""

    def test_macro_login_with_string_device_hash(self, test_client, setup_dual_products, db):
        """
        Macro login payload:
        {
            "login": "...",
            "password": "...",
            "product": "survival_macro",
            "device": {
                "machine_guid_hash": "<SHA256_STRING>",
                "device_name": "..."
            }
        }
        """
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import hash_password

        # Create client
        client_obj = Client(
            login="macroclient001",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        # Create license
        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=1,  # survival_macro
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)
        db.commit()

        # Exact Macro payload
        macro_device_hash = hashlib.sha256(
            "AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIII".encode()
        ).hexdigest()

        response = test_client.post(
            "/api/auth/login",
            json={
                "login": "macroclient001",
                "password": "password123",
                "product": "survival_macro",
                "device": {
                    "machine_guid_hash": macro_device_hash,
                    "device_name": "DESKTOP-TEST",
                },
            },
        )

        assert response.status_code == 200, response.json()
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["device_id"]

    def test_macro_verify_with_string_device_hash(self, test_client, setup_dual_products, db):
        """
        Macro verify payload:
        {
            "device_hash": "<SHA256_STRING>"
        }
        """
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import hash_password, create_access_token, hash_token

        # Setup
        client_obj = Client(
            login="macroclient002",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=1,
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)

        # Exact same hash as login
        macro_device_hash = hashlib.sha256(
            "AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIII".encode()
        ).hexdigest()

        from app.models import ClientSession

        token = create_access_token({"sub": "macroclient002", "client_id": client_obj.id})
        session = ClientSession(
            client_id=client_obj.id,
            token_hash=hash_token(token),
            refresh_token_hash=hash_token("dummy"),
            expires_at=now + timedelta(minutes=15),
            refresh_expires_at=now + timedelta(days=7),
            device_hash=hashlib.sha256(macro_device_hash.encode()).hexdigest(),
        )
        db.add(session)
        db.commit()

        # Exact Macro verify payload with STRING
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": macro_device_hash},
        )

        assert response.status_code == 200, response.json()
        data = response.json()
        assert data["valid"] is True
        assert data["login"] == "macroclient002"

    def test_macro_verify_string_format_validation(self, test_client, setup_dual_products, db):
        """String device_hash must be valid SHA-256 (64 hex chars)"""
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import hash_password, create_access_token, hash_token

        client_obj = Client(
            login="macroclient003",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=1,
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)
        db.commit()

        token = create_access_token({"sub": "macroclient003", "client_id": client_obj.id})

        # Invalid: too short
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": "abc123"},
        )
        assert response.status_code == 422

        # Invalid: invalid hex chars
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": "g" * 64},
        )
        assert response.status_code == 422


class TestVisionPayloads:
    """Vision sends dict with 5 component SHA-256 hashes in both login and verify"""

    def test_vision_login_with_dict_device_info(self, test_client, setup_dual_products, db):
        """
        Vision login payload:
        {
            "login": "...",
            "password": "...",
            "product": "survival_vision",
            "device": {
                "system_uuid_hash": "<SHA256>",
                "baseboard_serial_hash": "<SHA256>",
                "machine_guid_hash": "<SHA256>",
                "install_id_hash": "<SHA256>",
                "disk_serial_hash": "<SHA256>"
            }
        }
        """
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import hash_password

        client_obj = Client(
            login="visionclient001",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=2,  # survival_vision
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)
        db.commit()

        # Exact Vision payload with 5 hashes
        vision_device = {
            "system_uuid_hash": hashlib.sha256("uuid-001".encode()).hexdigest(),
            "baseboard_serial_hash": hashlib.sha256("bios-001".encode()).hexdigest(),
            "machine_guid_hash": hashlib.sha256("guid-001".encode()).hexdigest(),
            "install_id_hash": hashlib.sha256("install-001".encode()).hexdigest(),
            "disk_serial_hash": hashlib.sha256("disk-001".encode()).hexdigest(),
        }

        response = test_client.post(
            "/api/auth/login",
            json={
                "login": "visionclient001",
                "password": "password123",
                "product": "survival_vision",
                "device": vision_device,
            },
        )

        assert response.status_code == 200, response.json()
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["device_id"]

    def test_vision_verify_with_dict_device_hash(self, test_client, setup_dual_products, db):
        """
        Vision verify payload:
        {
            "device_hash": {
                "system_uuid_hash": "<SHA256>",
                "baseboard_serial_hash": "<SHA256>",
                "machine_guid_hash": "<SHA256>",
                "install_id_hash": "<SHA256>",
                "disk_serial_hash": "<SHA256>"
            }
        }
        """
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import hash_password, create_access_token, hash_token, hash_device

        client_obj = Client(
            login="visionclient002",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=2,
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)

        # Exact Vision device dict with 5 hashes
        vision_device = {
            "system_uuid_hash": hashlib.sha256("uuid-002".encode()).hexdigest(),
            "baseboard_serial_hash": hashlib.sha256("bios-002".encode()).hexdigest(),
            "machine_guid_hash": hashlib.sha256("guid-002".encode()).hexdigest(),
            "install_id_hash": hashlib.sha256("install-002".encode()).hexdigest(),
            "disk_serial_hash": hashlib.sha256("disk-002".encode()).hexdigest(),
        }

        from app.models import ClientSession

        token = create_access_token({"sub": "visionclient002", "client_id": client_obj.id})
        session = ClientSession(
            client_id=client_obj.id,
            token_hash=hash_token(token),
            refresh_token_hash=hash_token("dummy"),
            expires_at=now + timedelta(minutes=15),
            refresh_expires_at=now + timedelta(days=7),
            device_hash=hash_device(vision_device),
        )
        db.add(session)
        db.commit()

        # Exact Vision verify payload with DICT
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": vision_device},
        )

        assert response.status_code == 200, response.json()
        data = response.json()
        assert data["valid"] is True
        assert data["login"] == "visionclient002"

    def test_vision_verify_dict_format_validation(self, test_client, setup_dual_products, db):
        """Dict device_hash must have exactly 5 keys"""
        from app.models import Client
        from app.auth import hash_password, create_access_token

        client_obj = Client(
            login="visionclient003",
            password_hash=hash_password("password123"),
        )
        db.add(client_obj)
        db.flush()
        db.commit()

        token = create_access_token({"sub": "visionclient003", "client_id": client_obj.id})

        # Invalid: missing keys
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "device_hash": {
                    "machine_guid_hash": hashlib.sha256("guid".encode()).hexdigest(),
                }
            },
        )
        assert response.status_code == 422

        # Invalid: extra keys
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "device_hash": {
                    "system_uuid_hash": hashlib.sha256("uuid".encode()).hexdigest(),
                    "baseboard_serial_hash": hashlib.sha256("bios".encode()).hexdigest(),
                    "machine_guid_hash": hashlib.sha256("guid".encode()).hexdigest(),
                    "install_id_hash": hashlib.sha256("install".encode()).hexdigest(),
                    "disk_serial_hash": hashlib.sha256("disk".encode()).hexdigest(),
                    "extra_field": "invalid",
                }
            },
        )
        assert response.status_code == 422

        # Invalid: empty value
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "device_hash": {
                    "system_uuid_hash": "",
                    "baseboard_serial_hash": hashlib.sha256("bios".encode()).hexdigest(),
                    "machine_guid_hash": hashlib.sha256("guid".encode()).hexdigest(),
                    "install_id_hash": hashlib.sha256("install".encode()).hexdigest(),
                    "disk_serial_hash": hashlib.sha256("disk".encode()).hexdigest(),
                }
            },
        )
        assert response.status_code == 422


class TestDeviceMismatchValidation:
    """Device binding prevents mismatched devices"""

    def test_macro_device_mismatch_rejected(self, test_client, setup_dual_products, db):
        """Macro: different device_hash rejected"""
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import (
            hash_password,
            create_access_token,
            hash_token,
        )

        client_obj = Client(
            login="macroclient_mismatch",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=1,
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)

        device_hash_1 = hashlib.sha256("device-001".encode()).hexdigest()
        device_hash_2 = hashlib.sha256("device-002".encode()).hexdigest()

        from app.models import ClientSession

        token = create_access_token(
            {"sub": "macroclient_mismatch", "client_id": client_obj.id}
        )
        session = ClientSession(
            client_id=client_obj.id,
            token_hash=hash_token(token),
            refresh_token_hash=hash_token("dummy"),
            expires_at=now + timedelta(minutes=15),
            refresh_expires_at=now + timedelta(days=7),
            device_hash=hashlib.sha256(device_hash_1.encode()).hexdigest(),
        )
        db.add(session)
        db.commit()

        # Try verify with DIFFERENT device
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": device_hash_2},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "DEVICE_MISMATCH"

    def test_vision_device_mismatch_rejected(self, test_client, setup_dual_products, db):
        """Vision: different device dict rejected"""
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import (
            hash_password,
            create_access_token,
            hash_token,
            hash_device,
        )

        client_obj = Client(
            login="visionclient_mismatch",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=2,
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)

        device_1 = {
            "system_uuid_hash": hashlib.sha256("uuid-1".encode()).hexdigest(),
            "baseboard_serial_hash": hashlib.sha256("bios-1".encode()).hexdigest(),
            "machine_guid_hash": hashlib.sha256("guid-1".encode()).hexdigest(),
            "install_id_hash": hashlib.sha256("install-1".encode()).hexdigest(),
            "disk_serial_hash": hashlib.sha256("disk-1".encode()).hexdigest(),
        }

        device_2 = {
            "system_uuid_hash": hashlib.sha256("uuid-2".encode()).hexdigest(),
            "baseboard_serial_hash": hashlib.sha256("bios-2".encode()).hexdigest(),
            "machine_guid_hash": hashlib.sha256("guid-2".encode()).hexdigest(),
            "install_id_hash": hashlib.sha256("install-2".encode()).hexdigest(),
            "disk_serial_hash": hashlib.sha256("disk-2".encode()).hexdigest(),
        }

        from app.models import ClientSession

        token = create_access_token(
            {"sub": "visionclient_mismatch", "client_id": client_obj.id}
        )
        session = ClientSession(
            client_id=client_obj.id,
            token_hash=hash_token(token),
            refresh_token_hash=hash_token("dummy"),
            expires_at=now + timedelta(minutes=15),
            refresh_expires_at=now + timedelta(days=7),
            device_hash=hash_device(device_1),
        )
        db.add(session)
        db.commit()

        # Try verify with DIFFERENT device dict
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": device_2},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "DEVICE_MISMATCH"


class TestLogoutBothClients:
    """Both Macro and Vision logout revokes sessions"""

    def test_macro_logout_revokes_session(self, test_client, setup_dual_products, db):
        """Macro logout revokes token"""
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import hash_password, create_access_token, hash_token

        client_obj = Client(
            login="macroclient_logout",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=1,
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)

        from app.models import ClientSession

        token = create_access_token(
            {"sub": "macroclient_logout", "client_id": client_obj.id}
        )
        session = ClientSession(
            client_id=client_obj.id,
            token_hash=hash_token(token),
            refresh_token_hash=hash_token("dummy"),
            expires_at=now + timedelta(minutes=15),
            refresh_expires_at=now + timedelta(days=7),
            device_hash=hashlib.sha256("device".encode()).hexdigest(),
        )
        db.add(session)
        db.commit()

        # Logout
        response = test_client.post(
            "/api/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # Verify should fail
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": hashlib.sha256("device".encode()).hexdigest()},
        )
        assert response.status_code == 401

    def test_vision_logout_revokes_session(self, test_client, setup_dual_products, db):
        """Vision logout revokes token"""
        from app.models import Client, License, ClientStatus, LicenseType
        from app.auth import (
            hash_password,
            create_access_token,
            hash_token,
            hash_device,
        )

        client_obj = Client(
            login="visionclient_logout",
            password_hash=hash_password("password123"),
            status=ClientStatus.ACTIVE,
        )
        db.add(client_obj)
        db.flush()

        now = datetime.now(timezone.utc)
        license_obj = License(
            client_id=client_obj.id,
            product_id=2,
            license_type=LicenseType.TRIAL,
            device_limit=1,
            expires_at=now + timedelta(days=30),
            is_active=True,
        )
        db.add(license_obj)

        device = {
            "system_uuid_hash": hashlib.sha256("uuid".encode()).hexdigest(),
            "baseboard_serial_hash": hashlib.sha256("bios".encode()).hexdigest(),
            "machine_guid_hash": hashlib.sha256("guid".encode()).hexdigest(),
            "install_id_hash": hashlib.sha256("install".encode()).hexdigest(),
            "disk_serial_hash": hashlib.sha256("disk".encode()).hexdigest(),
        }

        from app.models import ClientSession

        token = create_access_token(
            {"sub": "visionclient_logout", "client_id": client_obj.id}
        )
        session = ClientSession(
            client_id=client_obj.id,
            token_hash=hash_token(token),
            refresh_token_hash=hash_token("dummy"),
            expires_at=now + timedelta(minutes=15),
            refresh_expires_at=now + timedelta(days=7),
            device_hash=hash_device(device),
        )
        db.add(session)
        db.commit()

        # Logout
        response = test_client.post(
            "/api/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # Verify should fail
        response = test_client.post(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_hash": device},
        )
        assert response.status_code == 401
