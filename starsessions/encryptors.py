import abc
import os
import warnings


class Encryptor(abc.ABC):
    def encrypt(self, data: bytes) -> bytes:
        raise NotImplementedError

    def decrypt(self, data: bytes) -> bytes:
        raise NotImplementedError


class NoopEncryptor(Encryptor):
    def encrypt(self, data: bytes) -> bytes:
        warnings.warn(
            "NoopEncryptor is not secure and should not be used in production. Please, configure a secure encryptor."
        )
        return data

    def decrypt(self, data: bytes) -> bytes:
        return data


class FernetEncryptor(Encryptor):
    def __init__(self, key: bytes):
        try:
            from cryptography.fernet import Fernet
        except ImportError:  # pragma: no cover
            raise ImportError("cryptography is required for FernetEncryptor")

        self.fernet = Fernet(key)
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self.fernet.decrypt(data)


class AESGCMEncryptor(Encryptor):
    def __init__(self, key: bytes):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:  # pragma: no cover
            raise ImportError("cryptography is required for AESGCMEncryptor")

        self.aesgcm = AESGCM(key)
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        if len(data) < 12:
            return b""
        nonce, ciphertext = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None)
