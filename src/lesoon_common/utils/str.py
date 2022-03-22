""" 基础工具模块."""
import re


def camelcase(udl_str: str, upper: bool = False):
    """
    下划线转换驼峰格式
    Args:
        udl_str: 下划线命名字符串
        upper: 是否转换为大驼峰

    """
    if not isinstance(udl_str, str):
        raise TypeError('camelcase() 只能接受str类型')
    parts = iter(udl_str.split('_'))
    first_word = '' if upper else next(parts)
    return first_word + ''.join(i.title() for i in parts)


def udlcase(hump_str: str):
    """
    驼峰转下划线格式
    Args:
        hump_str:  驼峰命名字符串

    """
    if not isinstance(hump_str, str):
        raise TypeError('udlcase() 只能接受str类型')
    udl_str = re.sub(r'([A-Z])', r'_\1', hump_str).lower()
    return udl_str.strip('_')
