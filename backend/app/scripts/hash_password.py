#!/usr/bin/env python3
"""
Script to generate password hash for admin.

Usage:
    python app/scripts/hash_password.py

This will prompt for a password and output the hash to use in .env
"""

import sys
from app.auth import hash_password


def main():
    print("=" * 60)
    print("ADMIN PASSWORD HASHER")
    print("=" * 60)
    print()

    password = input("Enter admin password: ").strip()
    if not password:
        print("ERROR: Password cannot be empty")
        sys.exit(1)

    confirm = input("Confirm password: ").strip()
    if password != confirm:
        print("ERROR: Passwords do not match")
        sys.exit(1)

    if len(password) < 8:
        print("ERROR: Password must be at least 8 characters")
        sys.exit(1)

    hash_value = hash_password(password)

    print()
    print("=" * 60)
    print("HASH GENERATED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("Copy this value to .env as ADMIN_PASSWORD_HASH:")
    print()
    print(f"ADMIN_PASSWORD_HASH={hash_value}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
