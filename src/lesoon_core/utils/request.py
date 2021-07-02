""" 请求处理模块."""
from functools import wraps
from typing import Callable

from sqlalchemy.orm.query import Query
from src.lesoon_core.parse.request import parse_request
from src.lesoon_core.parse.sqlalchemy import parse_multi_condition


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
        related_models = set()
        # 根据查询列查找涉及表实体
        for column in query.column_descriptions:
            related_models.add(column["entity"])

        # 根据关联查找关联表实体
        for join in query._legacy_setup_joins:
            related_models.add(join[0].entity_namespace)

        req = parse_request()
        filter_exp, sort_exp = parse_multi_condition(
            req.where, req.sort, related_models
        )
        query = query.filter(*filter_exp).order_by(*sort_exp)
        return query

    return wrapper
