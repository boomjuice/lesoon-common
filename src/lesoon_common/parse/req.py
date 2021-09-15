""" 请求参数过滤模块. """
import json
import re
import typing as t
from urllib import parse

from ..exceptions import ParseError


def extract_where_arg(where) -> t.Dict[str, str]:
    if where:
        try:
            # 特殊字符转义处理
            where = parse.unquote(where)
            _where = json.loads(where)
            if not isinstance(_where, dict):
                return dict()
            else:
                return _where
        except json.JSONDecodeError:
            raise ParseError(f"请求参数无法序列化 where:{where}")
    else:
        return dict()


def extract_sort_arg(sort) -> t.List[t.Tuple[str, int]]:
    if sort:
        if re.match(r"^[-,\w.]+$", sort):
            arg = []
            for s in sort.split(","):
                if s.startswith("-"):
                    # 倒序
                    arg.append((s[1:], -1))
                else:
                    # 正序
                    arg.append((s, 1))
            return arg
        else:
            return json.loads(sort)
    else:
        return list()
