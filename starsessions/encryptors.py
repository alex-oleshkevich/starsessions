import abc
import os
import warnings
from asyncio import to_thread


class Encryptor(abc.ABC):
    async def encrypt(self, data: bytes) -> bytes:
        raise NotImplementedError

    async def decrypt(self, data: bytes) -> bytes:
        raise NotImplementedError


class NoopEncryptor(Encryptor):
    async def encrypt(self, data: bytes) -> bytes:
        warnings.warn(
            "NoopEncryptor is not secure and should not be used in production. Please, configure a secure encryptor."
        )
        return data

    async def decrypt(self, data: bytes) -> bytes:
        return data


class FernetEncryptor(Encryptor):
    def __init__(self, key: bytes):
        try:
            from cryptography.fernet import Fernet
        except ImportError:  # pragma: no cover
            raise ImportError("cryptography is required for FernetEncryptor")

        self.fernet = Fernet(key)
        self.key = key

    async def encrypt(self, data: bytes) -> bytes:
        return await to_thread(self.fernet.encrypt, data)

    async def decrypt(self, data: bytes) -> bytes:
        return await to_thread(self.fernet.decrypt, data)


class AESGCMEncryptor(Encryptor):
    def __init__(self, key: bytes):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:  # pragma: no cover
            raise ImportError("cryptography is required for AESGCMEncryptor")

        self.aesgcm = AESGCM(key)
        self.key = key

    async def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        ciphertext = await to_thread(self.aesgcm.encrypt, nonce, data, None)
        return nonce + ciphertext

    async def decrypt(self, data: bytes) -> bytes:
        if len(data) < 12:
            return b""
        nonce, ciphertext = data[:12], data[12:]
        return await to_thread(self.aesgcm.decrypt, nonce, ciphertext, None)
