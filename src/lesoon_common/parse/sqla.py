""" Sqlalchemy解析模块.
将python对象解析成sqlalchemy对象以供查询
"""
import operator as sqla_op
import re
from typing import Any
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import Union

from flask_sqlalchemy import Model
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import expression as SqlaExp

from ..exceptions import ParseError
from ..utils.str import udlcase

SqlaExp = SqlaExp.BinaryExpression
SqlaExpList = List[SqlaExp]


def parse_multi_condition(
    where: dict, sort_list: list, models: Set[Type[Model]]
) -> Tuple[SqlaExpList, SqlaExpList]:
    """多表过滤条件解析."""
    filter_list = list()
    order_list = list()
    for model in models:
        _filter = parse_filter(where, model)
        _order = parse_sort(sort_list, model)
        filter_list.extend(_filter)
        order_list.extend(_order)

    return filter_list, order_list


def parse_filter(where: dict, model: Type[Model]) -> SqlaExpList:
    """过滤条件解析入口.
    : 将python str/json格式的过滤条件转化成sqlalchemy的过滤条件
    :param where: 查询过滤字典 {'a.status_eq': 1,'b.id': 2}
    :param model: sqlalchemy.Model
    """
    _filter = []
    if isinstance(where, dict) and len(where):
        _filter = parse_dictionary(where, model)
    return _filter


def parse_dictionary(where: dict, model: Type[Model]) -> SqlaExpList:
    """将过滤参数字典转换为sqlalchemy的过滤条件.

    :param filter_dict: 待转换字典 {"id_eq":"1"},{"a.id_lte":"2"}...
    :param model: sqlalchemy.Model
    """
    if len(where) == 0:
        return []

    conditions = []

    for column, value in where.items():
        column = parse_prefix_alias(column, model)
        if not column:
            continue
        new_filter = parse_suffix_operation(column, value, model)

        conditions.append(new_filter)

    return conditions


def parse_suffix_operation(
    column: str, value: Union[int, str, List[Any]], model: Type[Model]
) -> SqlaExp:
    op_mapper = {
        "eq": sqla_op.eq,
        "ne": sqla_op.ne,
        "lt": sqla_op.lt,
        "gt": sqla_op.gt,
        "lte": sqla_op.le,
        "gte": sqla_op.ge,
    }
    if m := re.match(r"(?P<col>[\w\\.]+)_(?P<op>[\w]+)", column):
        col, op = m.group("col"), m.group("op")
        attr = _parse_attribute_name(col, model)
        if op in op_mapper:
            return op_mapper[op](attr, value)
        elif op == "like":
            value = value if str(value).count("%") else f"%{value}%"
            return attr.like(value)
        elif op in ("in", "notin"):
            if isinstance(value, list):
                # 数组
                return getattr(attr, f"{op}_")(value)
            elif isinstance(value, str):
                # 逗号分隔字符串
                value_list: List[str] = value.strip().split(",")
                return getattr(attr, f"{op}_")(value_list)
            else:
                # 不支持in的类型
                raise ParseError(f"in不支持的类型{value}:{type(value)}")
        else:
            # 未定义的查询操作
            raise ParseError(f"无法解析的查询参数 {column}:{value}")
    else:
        attr = _parse_attribute_name(column, model)
        if isinstance(value, list):
            return attr.in_(value)
        else:
            return sqla_op.eq(attr, value)


def parse_prefix_alias(name: str, model: Type[Model]) -> Optional[str]:
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


def _parse_attribute_name(name: str, model: Type[Model]) -> InstrumentedAttribute:
    """根据 model,name获取模型的字段对象.
    :param model: sqlalchemy.Model
    :param name: 字段名
    :return: 返回字段名对应的Column实例对象
    """

    attr = getattr(model, udlcase(name))
    return attr


def parse_sort(sort_list: List[list], model: Type[Model]) -> SqlaExpList:
    """排序解析.
    :param sort_list: [('create_time',1),('status',-1)]
    :param model: flask_sqlalchemy.Model
    :return [create_time,status.desc()]
    """
    conditions: SqlaExpList = list()
    if not isinstance(sort_list, list) or sort_list is None:
        return conditions
    for sort_pair in sort_list:
        col, order = sort_pair[0], sort_pair[-1]
        col = parse_prefix_alias(col, model)
        if not col:
            continue
        attr = _parse_attribute_name(col, model)
        if order == -1:
            attr = attr.desc()
        conditions.append(attr)
    return conditions


def parse_related_models(query: Query) -> Set[Model]:
    """获取Query对象查询涉及的所有表"""
    related_models = set()
    # 根据查询列查找涉及表实体
    for column in query.column_descriptions:
        related_models.add(column["entity"])

    # 根据关联查找关联表实体
    for join in query._legacy_setup_joins:
        related_models.add(join[0].entity_namespace)
    return related_models
