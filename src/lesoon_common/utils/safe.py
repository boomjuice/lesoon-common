import hashlib


def generate_md5(__string: str):
    """生成md5串."""
    if not isinstance(__string, str):
        __string = str(__string)
    encrypt_plain = __string.encode("utf-8")
    m = hashlib.md5(encrypt_plain)
    return m.hexdigest()
