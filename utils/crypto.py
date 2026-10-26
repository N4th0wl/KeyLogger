"""
utils/crypto.py
Enkripsi dan dekripsi data menggunakan Fernet (AES-128-CBC + HMAC-SHA256).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def make_cipher(key: Optional[str]):
    """
    Buat instance Fernet dari key string.
    Kembalikan None jika key kosong (enkripsi dinonaktifkan).
    """
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        logger.error("Gagal membuat cipher Fernet: %s", exc)
        return None


def encrypt(data: bytes, cipher) -> bytes:
    """
    Enkripsi bytes. Kembalikan data asli jika cipher adalah None.
    """
    if cipher is None:
        return data
    return cipher.encrypt(data)


def decrypt(data: bytes, cipher) -> bytes:
    """
    Dekripsi bytes. Kembalikan data asli jika cipher adalah None.
    """
    if cipher is None:
        return data
    return cipher.decrypt(data)
