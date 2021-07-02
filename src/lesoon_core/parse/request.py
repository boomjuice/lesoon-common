"""

"""
import ast
import re

import werkzeug.exceptions
from flask import request

from ..exceptions import RequestParamError


class ParsedRequest:
    """请求解析类."""

    # `where` = query string (?where), 默认为None.
    where = None

    # `sort` = query string (?sort), 默认为None.
    sort = None

    # `page` = query string (?page), 默认为1.
    page = 1

    # `page_size` = query string (?page_size), 默认为25.
    page_size = 0

    # `args`  = request.args, 默认为None.
    args = None


def parse_request(payload=None) -> ParsedRequest:
    args = payload or request.args

    r = ParsedRequest()
    r.args = args

    r.where = extract_where_arg(args.get("where"))

    r.sort = extract_sort_arg(args.get("sort"))

    page_size_default = 25
    page_size_limit = 1000

    try:
        r.page_size = int(args["pageSize"])
        assert r.page_size > 0
        if r.page_size > page_size_limit:
            r.page_size = page_size_limit
    except (ValueError, werkzeug.exceptions.BadRequestKeyError, AssertionError):
        r.page_size = page_size_default

    try:
        r.page = abs(int(args.get("page") or 1))
        assert r.page > 0
    except (ValueError, werkzeug.exceptions.BadRequestKeyError, AssertionError):
        r.page = 1

    return r


def extract_where_arg(where):
    if where:
        try:
            return ast.literal_eval(where)
        except ValueError:
            raise RequestParamError(f"请求参数无法序列化 where:{where}")
    else:
        return None


def extract_sort_arg(sort):
    if sort:
        if re.match(r"^[-,\w.]+$", sort):
            arg = []
            for s in sort.split(","):
                if s.startswith("-"):
                    # 倒序
                    arg.append([s[1:], -1])
                else:
                    # 正序
                    arg.append([s])
            return arg
        else:
            return ast.literal_eval(sort)
    else:
        return None
