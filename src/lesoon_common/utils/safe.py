import base64
import hashlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import modes


def generate_md5(_input: str):
    """生成md5串."""
    if not isinstance(_input, str):
        _input = str(_input)
    encrypt_plain = _input.encode('utf-8')
    m = hashlib.md5(encrypt_plain)
    return m.hexdigest()


def base64url_decode(_input) -> str:
    """base64解密."""
    if isinstance(_input, str):
        _input = _input.encode()

    rem = len(_input) % 4

    if rem > 0:
        _input += b'=' * (4 - rem)

    return base64.urlsafe_b64decode(_input).decode()


def base64url_encode(_input) -> str:
    """base64加密."""
    if isinstance(_input, str):
        _input = _input.encode()
    return base64.urlsafe_b64encode(_input).replace(b'=', b'').decode()


def aes_cbc_encrpyt(key: str, _input: str) -> str:
    """AES/CBC/PKCS7对称加密."""
    if not isinstance(_input, str):
        raise TypeError('AES加密内容只能为字符串')

    key_bytes = key.encode()
    input_bytes = _input.encode()

    cipher = Cipher(algorithm=algorithms.AES(key_bytes),
                    mode=modes.CBC(key_bytes[:16]))

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_input = padder.update(input_bytes) + padder.finalize()

    encryptor = cipher.encryptor()
    encrypted_input = encryptor.update(padded_input) + encryptor.finalize()
    return base64.b64encode(encrypted_input).decode()


def aes_cbc_decrpyt(key: str, _input: str) -> str:
    """AES/CBC/PKCS7 对称解密."""
    if not isinstance(_input, str):
        raise TypeError('AES解密内容只能为字符串')

    key_bytes = key.encode()
    input_bytes = base64.b64decode(_input.encode())

    cipher = Cipher(algorithm=algorithms.AES(key_bytes),
                    mode=modes.CBC(key_bytes[:16]))

    decryptor = cipher.decryptor()
    dncrpyted_input = decryptor.update(input_bytes) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    unpadder_input = unpadder.update(dncrpyted_input) + unpadder.finalize()
    return unpadder_input.decode()
