""" 请求处理模块."""
from functools import wraps
from typing import Callable

from sqlalchemy.orm.query import Query

from ..parse.request import parse_request
from ..parse.sqlalchemy import parse_multi_condition
from ..parse.sqlalchemy import parse_related_models


def inject_sqla_condition(func: Callable[..., Query]) -> Callable[..., Query]:
    """注入查询过滤条件.
    : 将请求参数转化成sqlalchemy语法,注入函数返回的Query对象
    : 装饰函数返回值必须为Query子类，否则无法通过sqlalchemy语法注入
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        query = func(*args, **kwargs)
        if not isinstance(query, Query):
            raise TypeError(
                f"@inject_sqla_condition需要函数返回类型为{type(Query)},"
                f"{func.__module__}:{func.__name__}返回的类型为{type(query)}"
            )
        related_models = parse_related_models(query=query)
        req = parse_request()
        filter_exp, sort_exp = parse_multi_condition(
            req.where, req.sort, related_models
        )
        query = query.filter(*filter_exp).order_by(*sort_exp)
        return query

    return wrapper
