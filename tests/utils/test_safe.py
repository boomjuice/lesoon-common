import base64

import pytest

from lesoon_common.utils.safe import aes_cbc_decrpyt
from lesoon_common.utils.safe import aes_cbc_encrpyt
from lesoon_common.utils.safe import base64url_decode
from lesoon_common.utils.safe import base64url_encode


class TestSafeUtil:
    AES_KEY = 'U1NDUxNjQtNDgyMC00NjZiLTlkODgtMm'

    def test_base64_crypt(self):
        assert base64url_decode(base64url_encode('12345')) == '12345'

    def test_aes_encrypt_valid(self):
        with pytest.raises(TypeError):
            aes_cbc_encrpyt(self.AES_KEY, 123456)

    def test_aes_decrypt_valid(self):
        with pytest.raises(TypeError):
            aes_cbc_decrpyt(self.AES_KEY, 123456)

    def test_aes_encrypt(self):
        assert aes_cbc_encrpyt(self.AES_KEY,
                               '123456') == 'RO/nYDZmG6cEspG6D6gMog=='

    def test_aes_decrypt(self):
        assert aes_cbc_decrpyt(self.AES_KEY,
                               'RO/nYDZmG6cEspG6D6gMog==') == '123456'
