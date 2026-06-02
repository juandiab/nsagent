from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    return Fernet(settings.nsagent_encryption_key.encode())


def encrypt_value(plain_text: str) -> str:
    """Encrypt a string value using the Fernet key."""
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_value(cipher_text: str) -> str:
    """Decrypt a Fernet-encrypted string value."""
    return _get_fernet().decrypt(cipher_text.encode()).decode()
