#!/usr/bin/env python3
"""
Secure Admin Setup Script

This script:
1. Prompts for admin login and password (no echo)
2. Validates inputs
3. Generates bcrypt hash
4. Generates random JWT_SECRET
5. Updates .env file with proper validation
6. Never stores credentials in code or default values

Usage:
    python app/scripts/setup_admin.py
"""

import sys
import os
import secrets
import getpass
from pathlib import Path
from app.auth import hash_password


def read_env_file(env_path):
    """Read .env file and return as dict"""
    env_dict = {}
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    env_dict[key.strip()] = value.strip()
    return env_dict


def write_env_file(env_path, env_dict):
    """Write env dict back to .env file preserving format"""
    with open(env_path, 'w', encoding='utf-8') as f:
        for key, value in env_dict.items():
            if value:
                f.write(f"{key}={value}\n")
            else:
                f.write(f"{key}=\n")


def generate_jwt_secret():
    """Generate a secure random JWT secret (32 bytes = 64 hex chars)"""
    return secrets.token_hex(32)


def main():
    print("\n" + "=" * 70)
    print("SURVIVAL MACRO - ADMIN SETUP")
    print("=" * 70)
    print()
    print("This script will configure admin credentials securely.")
    print("Passwords are not echoed. Do not paste from clipboard.")
    print()

    # Get .env path
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent.parent
    env_path = backend_dir / ".env"

    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}")
        print("Create .env from .env.example first")
        sys.exit(1)

    print(f"Target: {env_path}")
    print()

    # 1. Get login
    while True:
        login = input("Enter admin login (3-50 chars): ").strip()
        if 3 <= len(login) <= 50:
            if all(c.isalnum() or c in '_-' for c in login):
                break
            else:
                print("ERROR: Login must contain only alphanumeric, _, or -")
        else:
            print("ERROR: Login must be 3-50 characters")

    print()

    # 2. Get password (no echo)
    while True:
        password = getpass.getpass("Enter admin password (min 8 chars): ")
        if len(password) < 8:
            print("ERROR: Password must be at least 8 characters")
            continue

        confirm = getpass.getpass("Confirm password: ")
        if password == confirm:
            break
        else:
            print("ERROR: Passwords do not match")

    print()

    # 3. Generate hash
    print("Generating password hash (bcrypt)...")
    password_hash = hash_password(password)
    print("OK")

    # 4. Generate JWT secret
    print("Generating JWT secret...")
    jwt_secret = generate_jwt_secret()
    print("OK")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Login: {login}")
    print(f"Password hash: {password_hash[:20]}...{password_hash[-10:]}")
    print(f"JWT Secret: {jwt_secret[:20]}...{jwt_secret[-10:]}")
    print()

    confirm_write = input("Write to .env? (yes/no): ").strip().lower()
    if confirm_write not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)

    print()

    # 5. Update .env
    try:
        env_dict = read_env_file(env_path)
        env_dict['ADMIN_LOGIN'] = login
        env_dict['ADMIN_PASSWORD_HASH'] = password_hash
        env_dict['JWT_SECRET'] = jwt_secret

        write_env_file(env_path, env_dict)
        print("Updated .env successfully")
    except Exception as e:
        print(f"ERROR writing .env: {e}")
        sys.exit(1)

    # 6. Verify
    try:
        env_dict = read_env_file(env_path)
        if env_dict.get('ADMIN_LOGIN') == login:
            print("Verification: OK")
        else:
            print("WARNING: .env read-back mismatch")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR verifying .env: {e}")
        sys.exit(1)

    print()
    print("=" * 70)
    print("ADMIN CONFIGURED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Start backend: python main.py")
    print("2. Backend will initialize database")
    print("3. Access admin at: http://localhost:5175")
    print("4. Login with configured credentials")
    print()


if __name__ == "__main__":
    main()
