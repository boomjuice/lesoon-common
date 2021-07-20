""" 基础工具模块."""
import re


def camelcase(udl_str: str):
    """下划线转换驼峰格式"""
    if not isinstance(udl_str, str):
        raise TypeError("camelcase() 只能接受str类型")
    parts = iter(udl_str.split("_"))
    return next(parts) + "".join(i.title() for i in parts)


def udlcase(hump_str: str):
    """驼峰转下划线格式"""
    if not isinstance(hump_str, str):
        raise TypeError("udlcase() 只能接受str类型")
    udl_str = re.sub(r"([A-Z])", r"_\1", hump_str).lower()
    return udl_str
