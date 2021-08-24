import random
import string
import time
import typing as t


def generate_id(size: int = 18) -> str:
    """根据时间戳加随机整数生成id."""
    if size < 14:
        raise ValueError("根据时间戳生成的id长度必须在14以上")
    else:
        curr_ts = int(time.time() * 1000)
        num_of_numeric = size + 1 - 14
        random_id = str(curr_ts) + random_numeric(num_of_numeric)
        return random_id


def _random_char_list(size: int, char_set: str) -> t.List[str]:
    char_list = random.choices(population=char_set, k=size)
    return char_list


def random_numeric(size: int) -> str:
    return "".join(_random_char_list(size=size, char_set=string.digits))


def random_alpha(size: int) -> str:
    return "".join(_random_char_list(size=size, char_set=string.ascii_letters))


def random_alpha_numeric(size: int) -> str:
    return "".join(
        _random_char_list(size=size, char_set=string.digits + string.ascii_letters)
    )
