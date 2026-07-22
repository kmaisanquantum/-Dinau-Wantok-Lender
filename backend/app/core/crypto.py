"""
Identity hashing and PII field encryption.

Design intent:
- Phone numbers / national IDs are NEVER stored in plaintext anywhere,
  including in logs. They are normalized, peppered, and SHA-256 hashed
  before touching the database. The hash is deterministic (same input
  -> same hash) so it can be used as a cross-tenant lookup key for
  fraud flags, WITHOUT the reverse being possible.
- Everything else that identifies a person (name, address, employer)
  is tenant-scoped and encrypted at rest with AES-GCM, decrypted only
  inside the tenant's own request context.
"""
import base64
import hashlib
import os
import re

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def normalize_phone(raw_phone: str, default_country_code: str = "675") -> str:
    """Normalize a PNG phone number to a consistent E.164-ish digit string
    so the same person hashes identically regardless of how the number
    was entered (with/without +675, spaces, leading 0, etc)."""
    digits = re.sub(r"\D", "", raw_phone)
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith(default_country_code):
        return digits
    if digits.startswith("0"):
        digits = digits[1:]
    return f"{default_country_code}{digits}"


def hash_identifier(value: str) -> str:
    """SHA-256(hex) of a normalized identifier + server-side pepper.
    Deterministic on purpose — this is a lookup key, not a password hash."""
    peppered = f"{value}:{settings.hash_pepper}".encode("utf-8")
    return hashlib.sha256(peppered).hexdigest()


def hash_phone(raw_phone: str) -> str:
    return hash_identifier(normalize_phone(raw_phone))


def hash_national_id(raw_id: str) -> str:
    cleaned = re.sub(r"\s+", "", raw_id).upper()
    return hash_identifier(cleaned)


# --- Field-level AES-GCM encryption for tenant-scoped PII -----------------

def _key_bytes() -> bytes:
    key = base64.b64decode(settings.field_encryption_key)
    if len(key) != 32:
        raise RuntimeError(
            "field_encryption_key must decode to exactly 32 bytes (AES-256). "
            "Generate one with: python -c \"import os,base64;print(base64.b64encode(os.urandom(32)).decode())\""
        )
    return key


def encrypt_field(plaintext: str) -> bytes:
    if plaintext is None:
        return None
    aesgcm = AESGCM(_key_bytes())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext  # store nonce prefixed to ciphertext


def decrypt_field(blob: bytes) -> str:
    if blob is None:
        return None
    aesgcm = AESGCM(_key_bytes())
    nonce, ciphertext = blob[:12], blob[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


# --- Password Hashing -----------------
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
