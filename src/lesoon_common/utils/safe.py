import base64
import hashlib


def generate_md5(_input: str):
    """生成md5串."""
    if not isinstance(_input, str):
        _input = str(_input)
    encrypt_plain = _input.encode("utf-8")
    m = hashlib.md5(encrypt_plain)
    return m.hexdigest()


def base64url_decode(_input) -> str:
    if isinstance(_input, str):
        _input = _input.encode()

    rem = len(_input) % 4

    if rem > 0:
        _input += b"=" * (4 - rem)

    return base64.urlsafe_b64decode(_input).decode()


def base64url_encode(_input) -> str:
    if isinstance(_input, str):
        _input = _input.encode()
    return base64.urlsafe_b64encode(_input).replace(b"=", b"").decode()
