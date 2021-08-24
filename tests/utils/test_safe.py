import pytest

from lesoon_common.utils.safe import aes_cbc_decrpyt
from lesoon_common.utils.safe import aes_cbc_encrpyt


class TestSafeUtil:
    AES_KEY = "U1NDUxNjQtNDgyMC00NjZiLTlkODgtMm"

    def test_aes_encrypt_valid(self):
        with pytest.raises(TypeError):
            aes_cbc_encrpyt(self.AES_KEY, 123456)

    def test_aes_decrypt_valid(self):
        with pytest.raises(TypeError):
            aes_cbc_decrpyt(self.AES_KEY, 123456)

    def test_aes_encrypt(self):
        assert aes_cbc_encrpyt(self.AES_KEY, "123456") == "RO/nYDZmG6cEspG6D6gMog=="

    def test_aes_decrypt(self):
        assert aes_cbc_decrpyt(self.AES_KEY, "RO/nYDZmG6cEspG6D6gMog==") == "123456"
