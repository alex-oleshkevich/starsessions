import pytest

from starsessions.encryptors import AESGCMEncryptor, FernetEncryptor, NoopEncryptor


@pytest.fixture
def aes_key() -> bytes:
    return b"\x00" * 32


@pytest.fixture
def fernet_key() -> bytes:
    from cryptography.fernet import Fernet

    return Fernet.generate_key()


def test_noop_round_trip() -> None:
    enc = NoopEncryptor()
    with pytest.warns(UserWarning, match="NoopEncryptor"):
        assert enc.decrypt(enc.encrypt(b"hello")) == b"hello"


class TestFernetEncryptor:
    def test_fernet_round_trip(self, fernet_key: bytes) -> None:
        enc = FernetEncryptor(fernet_key)
        plaintext = b'{"user": "alice", "role": "admin"}'
        assert enc.decrypt(enc.encrypt(plaintext)) == plaintext

    def test_fernet_produces_unique_ciphertexts(self, fernet_key: bytes) -> None:
        """Fernet uses a random IV; encrypting the same plaintext twice must differ."""
        enc = FernetEncryptor(fernet_key)
        plaintext = b"same data"
        ct1 = enc.encrypt(plaintext)
        ct2 = enc.encrypt(plaintext)
        assert ct1 != ct2


class TestAESGCMEncryptor:
    def test_aesgcm_round_trip(self, aes_key: bytes) -> None:
        enc = AESGCMEncryptor(aes_key)
        plaintext = b'{"user": "bob", "role": "user"}'
        assert enc.decrypt(enc.encrypt(plaintext)) == plaintext

    def test_aesgcm_nonce_is_random(self, aes_key: bytes) -> None:
        enc = AESGCMEncryptor(aes_key)
        plaintext = b"same secret data"
        ct1 = enc.encrypt(plaintext)
        ct2 = enc.encrypt(plaintext)
        assert ct1 != ct2


def test_aesgcm_empty_decrypt_returns_empty(aes_key: bytes) -> None:
    """Too-short input (< 12 bytes nonce) must not raise, just return empty."""
    enc = AESGCMEncryptor(aes_key)
    assert enc.decrypt(b"") == b""
    assert enc.decrypt(b"short") == b""


def test_aesgcm_wrong_key_raises(aes_key: bytes) -> None:
    """Decrypting with a different key must fail (authentication tag mismatch)."""
    from cryptography.exceptions import InvalidTag

    enc = AESGCMEncryptor(aes_key)
    other_enc = AESGCMEncryptor(b"\xff" * 32)
    ciphertext = enc.encrypt(b"secret")
    with pytest.raises(InvalidTag):
        other_enc.decrypt(ciphertext)
