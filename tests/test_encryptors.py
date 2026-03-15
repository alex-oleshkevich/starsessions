import pytest

from starsessions.encryptors import AESGCMEncryptor, FernetEncryptor, NoopEncryptor


@pytest.fixture
def aes_key() -> bytes:
    # AESGCM requires 16, 24, or 32 byte key
    return b"\x00" * 32


@pytest.fixture
def fernet_key() -> bytes:
    from cryptography.fernet import Fernet

    return Fernet.generate_key()


@pytest.mark.asyncio
async def test_noop_round_trip() -> None:
    enc = NoopEncryptor()
    with pytest.warns(UserWarning, match="NoopEncryptor"):
        assert await enc.decrypt(await enc.encrypt(b"hello")) == b"hello"


class TestFernetEncryptor:
    @pytest.mark.asyncio
    async def test_fernet_round_trip(self, fernet_key: bytes) -> None:
        enc = FernetEncryptor(fernet_key)
        plaintext = b'{"user": "alice", "role": "admin"}'
        assert await enc.decrypt(await enc.encrypt(plaintext)) == plaintext

    @pytest.mark.asyncio
    async def test_fernet_produces_unique_ciphertexts(self, fernet_key: bytes) -> None:
        """Fernet uses a random IV; encrypting the same plaintext twice must differ."""
        enc = FernetEncryptor(fernet_key)
        plaintext = b"same data"
        ct1 = await enc.encrypt(plaintext)
        ct2 = await enc.encrypt(plaintext)
        assert ct1 != ct2


class TestAESGCMEncryptor:
    @pytest.mark.asyncio
    async def test_aesgcm_round_trip(self, aes_key: bytes) -> None:
        enc = AESGCMEncryptor(aes_key)
        plaintext = b'{"user": "bob", "role": "user"}'
        assert await enc.decrypt(await enc.encrypt(plaintext)) == plaintext

    @pytest.mark.asyncio
    async def test_aesgcm_nonce_is_random(self, aes_key: bytes) -> None:
        enc = AESGCMEncryptor(aes_key)
        plaintext = b"same secret data"
        ct1 = await enc.encrypt(plaintext)
        ct2 = await enc.encrypt(plaintext)

        # different ciphertexts because of different nonces
        assert ct1 != ct2


@pytest.mark.asyncio
async def test_aesgcm_empty_decrypt_returns_empty(aes_key: bytes) -> None:
    """Too-short input (< 12 bytes nonce) must not raise, just return empty."""
    enc = AESGCMEncryptor(aes_key)
    assert await enc.decrypt(b"") == b""
    assert await enc.decrypt(b"short") == b""


@pytest.mark.asyncio
async def test_aesgcm_wrong_key_raises(aes_key: bytes) -> None:
    """Decrypting with a different key must fail (authentication tag mismatch)."""
    from cryptography.exceptions import InvalidTag

    enc = AESGCMEncryptor(aes_key)
    other_enc = AESGCMEncryptor(b"\xff" * 32)
    ciphertext = await enc.encrypt(b"secret")
    with pytest.raises(InvalidTag):
        await other_enc.decrypt(ciphertext)
