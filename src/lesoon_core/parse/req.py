""" 请求参数过滤模块. """
import ast
import re
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ..exceptions import RequestParamError


def extract_where_arg(where) -> Optional[Dict[str, str]]:
    if where:
        try:
            return ast.literal_eval(where)
        except ValueError:
            raise RequestParamError(f"请求参数无法序列化 where:{where}")
    else:
        return None


def extract_sort_arg(sort) -> Optional[List[Tuple[str, int]]]:
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
            return ast.literal_eval(sort)
    else:
        return None
