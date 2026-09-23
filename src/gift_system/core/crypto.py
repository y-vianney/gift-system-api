from __future__ import annotations


import hashlib
import os
import secrets
import string
from cryptography.fernet import Fernet, InvalidToken

DEFAULT_SALT = os.getenv("GS_KEY_SALT", "gift-system-secret-salt-2026")


def normalize_key(key: str) -> str:
    """normalize input key (strip whitespace, uppercase)."""
    return key.strip().upper()


def generate_private_key(prefix: str = "") -> str:
    """
    generate a clean, easy-to-type, cryptographically secure private key
    format: 2 uppercase letters + 3 digits
    """
    letters = string.ascii_uppercase
    digits = string.digits
    token = (
        secrets.choice(letters)
        + secrets.choice(letters)
        + "".join(secrets.choice(digits) for _ in range(3))
    )
    return f"{prefix}{token}"


def hash_key(key: str, salt: str = DEFAULT_SALT) -> str:
    """compute salted SHA-256 hash of normalized key for secure database storage"""
    norm = normalize_key(key)
    return hashlib.sha256(f"{norm}:{salt}".encode("utf-8")).hexdigest()


def generate_thread_key() -> str:
    """generate a new url-safe Fernet encryption key for conversation thread confidentiality"""
    return Fernet.generate_key().decode("utf-8")


def encrypt_message(plain_text: str, thread_key: str) -> str:
    """encrypt message text using Fernet (AES-128-CBC with HMAC-SHA256)"""
    f = Fernet(thread_key.encode("utf-8"))
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_message(cipher_text: str, thread_key: str) -> str | None:
    """decrypt message text using Fernet. Returns None if decryption fails or token is invalid"""
    try:
        f = Fernet(thread_key.encode("utf-8"))
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        return None
