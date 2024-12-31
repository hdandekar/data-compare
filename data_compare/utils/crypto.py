from cryptography.fernet import Fernet

from config.settings.base import ENCRYPTION_KEY


def encrypt_password(password):
    key = ENCRYPTION_KEY
    f = Fernet(key)
    byte_password = bytes(password, "utf-8")
    encrypted_password = f.encrypt(byte_password).decode("utf-8")
    return encrypted_password


def decrypt_password(password):
    key = ENCRYPTION_KEY
    f = Fernet(key)
    decrypted_password = f.decrypt(password).decode("utf-8")
    return decrypted_password
