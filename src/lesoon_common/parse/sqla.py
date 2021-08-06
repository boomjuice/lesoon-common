""" Sqlalchemy解析模块.
将python对象解析成sqlalchemy对象以供查询
"""
import abc
import operator as sqla_op
import re
import typing as t

from flask_sqlalchemy import Model
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import expression as SqlaExp
from sqlalchemy.sql.annotation import Annotated

from ..exceptions import ParseError
from ..utils.str import udlcase

SqlaExp = SqlaExp.BinaryExpression
SqlaExpList = t.List[SqlaExp]


def parse_multi_condition(
    where: dict, sort_list: list, models: t.Set[t.Type[Model]]
) -> t.Tuple[SqlaExpList, SqlaExpList]:
    """多表过滤条件解析."""
    filter_list = list()
    order_list = list()
    for model in models:
        _filter = parse_filter(where, model)
        _order = parse_sort(sort_list, model)
        filter_list.extend(_filter)
        order_list.extend(_order)

    return filter_list, order_list


def parse_filter(where: dict, model: t.Type[Model]) -> SqlaExpList:
    """将过滤参数字典转换为sqlalchemy的过滤条件.

    :param where: 待转换字典 {"id_eq":"1"},{"a.id_lte":"2"}...
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


def parse_sort(sort_list: t.List[list], model: t.Type[Model]) -> SqlaExpList:
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


class SqlaOpParser(metaclass=abc.ABCMeta):
    def __init__(
        self,
        column: InstrumentedAttribute,
        operate: str,
        value: t.Union[int, str, t.List[t.Any]],
    ):
        self.column = column
        self.operate = operate
        self.value = value

    @abc.abstractmethod
    def parse(self):
        pass


class CmprParser(SqlaOpParser):
    comparison_mapper = {
        "eq": sqla_op.eq,
        "ne": sqla_op.ne,
        "lt": sqla_op.lt,
        "gt": sqla_op.gt,
        "lte": sqla_op.le,
        "gte": sqla_op.ge,
    }

    def parse(self):
        cmpr_op = self.comparison_mapper[self.operate]
        return cmpr_op(self.column, self.value)


class InParser(SqlaOpParser):
    in_mapper = {"in": "in_", "notIn": "notin_"}

    def parse(self):
        attr_op = self.in_mapper[self.operate]
        if isinstance(self.value, list):
            # 数组
            return getattr(self.column, attr_op)(self.value)
        elif isinstance(self.value, str):
            # 逗号分隔字符串
            value_list: t.List[str] = self.value.strip().split(",")
            return getattr(self.column, attr_op)(value_list)
        else:
            raise ParseError(f"{attr_op} 不支持的类型{self.value}:{type(self.value)}")


class LikeParser(SqlaOpParser):
    like_mapper = {
        "like": "like",
        "ilike": "ilike",
        "notLike": "not_like",
        "notIlike": "not_ilike",
    }

    def parse(self):
        attr_op = self.like_mapper[self.operate]
        value = self.value if str(self.value).count("%") else f"%{self.value}%"
        return getattr(self.column, attr_op)(value)


class OpParserFactory:
    @classmethod
    def create(
        cls,
        column: InstrumentedAttribute,
        operate: str,
        value: t.Union[int, str, t.List[t.Any]],
    ) -> SqlaOpParser:
        if operate in CmprParser.comparison_mapper:
            return CmprParser(column, operate, value)

        elif operate.lower().count("like"):
            return LikeParser(column, operate, value)

        elif operate.lower().count("in"):
            return InParser(column, operate, value)
        else:
            # 未定义的查询操作
            raise ParseError(f"无法解析的查询参数 {column}:{value}")


def parse_prefix_alias(name: str, model: t.Type[Model]) -> t.Optional[str]:
    """匹配过滤参数的表别名前缀.
    :param model: sqlalchemy.Model
    :param name: model.field.name
    """
    name_split = name.split(".")
    if len(name_split) > 2:
        raise ParseError(f"过滤列名不合法: {name}")
    elif len(name_split) == 2:
        if isinstance(model, AliasedClass):
            model_alias = model._aliased_insp.name
        elif isinstance(model, Annotated):
            model_alias = model.name
        else:
            model_alias = None
        alias, column = name_split
        if alias == model_alias:  # noqa
            # 过滤参数别名与model别名匹配
            return column
        else:
            # 不匹配
            return None
    else:
        # 非别名过滤
        return name


def parse_suffix_operation(
    column: str, value: t.Union[int, str, t.List[t.Any]], model: t.Type[Model]
) -> SqlaExp:
    if m := re.match(r"(?P<col>[\w\\.]+)_(?P<op>[\w]+)", column):
        col, op = m.group("col"), m.group("op")
        attr = _parse_attribute_name(col, model)
        return OpParserFactory.create(attr, op, value).parse()
    else:
        attr = _parse_attribute_name(column, model)
        if isinstance(value, list):
            return attr.in_(value)
        else:
            return sqla_op.eq(attr, value)


def _parse_attribute_name(name: str, model: t.Type[Model]) -> InstrumentedAttribute:
    """根据 model,name获取模型的字段对象.
    :param model: sqlalchemy.Model
    :param name: 字段名
    :return: 返回字段名对应的Column实例对象
    """
    if isinstance(model, Annotated):
        attr = getattr(model.columns, udlcase(name))
    else:
        attr = getattr(model, udlcase(name))
    return attr


def parse_related_models(query: Query) -> t.Set[Model]:
    """获取Query对象查询涉及的所有表"""
    related_models = set()
    # 根据查询列查找涉及表实体
    for column in query.column_descriptions:
        related_models.add(column["entity"])

    # 根据关联查找关联表实体
    for join in query._legacy_setup_joins:
        join_obj = join[0].entity_namespace
        if isinstance(join_obj, t.Hashable):
            related_models.add(join_obj)
    return related_models
