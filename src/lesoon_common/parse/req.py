""" 请求参数过滤模块. """
import json
import re
import typing as t
from urllib import parse

from lesoon_common.exceptions import ParseError


def extract_where_arg(where: t.Optional[str] = None) -> t.Dict[str, str]:
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
            raise ParseError(f'请求参数无法序列化 where:{where}')
    else:
        return dict()


def extract_sort_arg(sort: t.Optional[str] = None) -> t.List[t.Tuple[str, str]]:
    if sort:
        if re.match(r'[,\w]+ ((asc)|(desc))', sort):
            arg = []
            for s in sort.split(','):
                # s = 'id asc' or 'id desc'
                col, order = s.split(' ', 1)
                arg.append((col, order))
            return arg
        else:
            try:
                return json.loads(sort)
            except json.JSONDecodeError:
                return list()
    else:
        return list()
