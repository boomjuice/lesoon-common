import base64
import hashlib


def generate_md5(input: str):
    """生成md5串."""
    if not isinstance(input, str):
        input = str(input)
    encrypt_plain = input.encode("utf-8")
    m = hashlib.md5(encrypt_plain)
    return m.hexdigest()


def base64url_decode(input) -> str:
    if isinstance(input, str):
        input = input.encode()

    rem = len(input) % 4

    if rem > 0:
        input += b"=" * (4 - rem)

    return base64.urlsafe_b64decode(input).decode()


def base64url_encode(input) -> str:
    if isinstance(input, str):
        input = input.encode()
    return base64.urlsafe_b64encode(input).replace(b"=", b"").decode()
