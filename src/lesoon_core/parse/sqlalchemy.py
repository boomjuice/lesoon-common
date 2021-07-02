""" 解析模块.
将python对象解析成sqlalchemy对象以供查询
"""
import operator as sqla_op
import re
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from flask_sqlalchemy import Model
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import expression as sqla_exp

from ..exceptions import ParseError
from ..utils.base import udlcase

SQLA_EXP = sqla_exp.BinaryExpression
SQLA_EXP_LIST = List[SQLA_EXP]


def parse_multi_condition(
    where_list, sort_list, models: Set[Model]
) -> Tuple[SQLA_EXP_LIST, SQLA_EXP_LIST]:
    """多表过滤条件解析."""
    filter_list = list()
    order_list = list()
    for model in models:
        _filter = parse_filter(where_list, model)
        _order = parse_sort(sort_list, model)
        filter_list.extend(_filter)
        order_list.extend(_order)

    return filter_list, order_list


def parse_filter(_filter: dict, model: Model) -> SQLA_EXP_LIST:
    """过滤条件解析入口.
    : 将python str/json格式的过滤条件转化成sqlalchemy的过滤条件
    """
    if _filter is None or len(_filter) == 0:
        _filter = []
    elif isinstance(_filter, dict):
        _filter = parse_dictionary(_filter, model)
    return _filter


def parse_dictionary(filter_dict: dict, model: Model) -> SQLA_EXP_LIST:
    """将过滤参数字典转换为sqlalchemy的过滤条件.

    :param filter_dict: 待转换字典 {"id_eq":"1"},{"a.id_lte":"2"}...
    :param model: sqlalchemy.Model
    """
    if len(filter_dict) == 0:
        return []

    conditions = []

    for column, value in filter_dict.items():
        column = parse_prefix_alias(model, column)
        if not column:
            continue
        new_filter = parse_suffix_operation(column, value, model)

        conditions.append(new_filter)

    return conditions


def parse_suffix_operation(
    column: str, value: Union[str, int], model: Model
) -> SQLA_EXP:
    op_mapper = {
        "eq": sqla_op.eq,
        "ne": sqla_op.ne,
        "lt": sqla_op.lt,
        "gt": sqla_op.gt,
        "lte": sqla_op.le,
        "gte": sqla_op.ge,
    }
    if m := re.match(r"(?P<col>[\w\\.]+)_(?P<op>[\w]+)", column):
        col, op = udlcase(m.group("col")), m.group("op")
        attr = _parse_attribute_name(model, col)
        if op in op_mapper:
            return op_mapper[op](attr, value)
        elif op == "like":
            value = value if value.count("%") else f"%{value}%"
            return attr.like(value)
        elif op == "in":
            value = value.strip().split(",")
            return attr.in_(value)
        else:
            raise ParseError(f"无法解析的查询参数 {column}:{value}")
    else:
        attr = _parse_attribute_name(model, udlcase(column))
        return sqla_op.eq(attr, value)


def parse_prefix_alias(model: Model, name: str) -> Optional[str]:
    """匹配过滤参数的表别名前缀.
    :param model: sqlalchemy.Model
    :param name: model.field.name
    """
    name_split = name.split(".")
    if len(name_split) > 2:
        raise ParseError(f"过滤列名不合法: {name}")
    elif len(name_split) == 2 and isinstance(model, AliasedClass):
        alias, column = name_split
        if alias == model._aliased_insp.name:  # noqa
            # 过滤参数别名与model别名匹配
            return column
        else:
            # 不匹配
            return None
    else:
        # 非别名过滤
        return name


def _parse_attribute_name(model: Model, name: str) -> InstrumentedAttribute:
    """根据 model,name获取模型的字段对象.
    :param model: sqlalchemy.Model
    :param name: model.field.name
    :return: model.field
    """

    attr = getattr(model, udlcase(name))
    return attr


def parse_sort(sort_list: List[list], model: Model) -> SQLA_EXP_LIST:
    """排序解析.
    :param sort_list: [['create_time'],['status',-1]]
    :param model: flask_sqlalchemy.Model
    :return [create_time,status.desc()]
    """
    conditions = list()
    if not isinstance(sort_list, list) or sort_list is None:
        return conditions
    for sort_pair in sort_list:
        col, order = sort_pair[0], sort_pair[-1]
        col = parse_prefix_alias(model, col)
        if not col:
            continue
        attr = _parse_attribute_name(model, col)
        if order == -1:
            attr = attr.desc()
        conditions.append(attr)
    return conditions
