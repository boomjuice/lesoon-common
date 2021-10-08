""" Sqlalchemy解析模块.
将python对象解析成sqlalchemy对象以供查询
"""
import abc
import operator as sqla_op
import re
import typing as t

from flask_sqlalchemy import Model
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm.util import _ORMJoin
from sqlalchemy.sql import expression as SqlaExp
from sqlalchemy.sql.annotation import Annotated
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.schema import Table
from sqlalchemy.sql.selectable import Alias
from sqlalchemy.sql.selectable import Select
from sqlalchemy.sql.selectable import Subquery

from lesoon_common.exceptions import ParseError
from lesoon_common.utils.str import udlcase

SqlaExp = SqlaExp.BinaryExpression
SqlaExpList = t.List[SqlaExp]


def parse_multi_condition(
        where: dict, sort_list: list,
        models: t.List[t.Union[Table,
                               Alias]]) -> t.Tuple[SqlaExpList, SqlaExpList]:
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
    conditions: SqlaExpList = list()
    if len(where) == 0:
        return conditions

    for key, value in list(where.items()):
        column = parse_prefix_alias(key, model)
        if not column:
            continue
        condition = parse_suffix_operation(column, value, model)
        if isinstance(condition, SqlaExp):
            conditions.append(condition)
            # 匹配上就剔除过滤条件
            del where[key]

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

    for sort_pair in sort_list.copy():
        col, order = sort_pair[0], sort_pair[-1]
        col = parse_prefix_alias(col, model)
        if col is None:
            continue
        if (attr := parse_attribute_name(col, model)) is not None:
            conditions.append(attr.desc() if order == "desc" else attr)
            # 匹配上就剔除过滤条件
            sort_list.remove(sort_pair)

    return conditions


class SqlaOpParser(metaclass=abc.ABCMeta):
    op_dict: t.Dict[str, t.Any] = dict()

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


class CmpOpParser(SqlaOpParser):
    op_dict = {
        "eq": sqla_op.eq,
        "ne": sqla_op.ne,
        "lt": sqla_op.lt,
        "gt": sqla_op.gt,
        "lte": sqla_op.le,
        "gte": sqla_op.ge,
    }

    def parse(self):
        cmp_op = self.op_dict[self.operate]
        return cmp_op(self.column, self.value)


class InOpParser(SqlaOpParser):
    op_dict = {"in": "in_", "notIn": "notin_"}

    def parse(self):
        attr_op = self.op_dict[self.operate]
        if isinstance(self.value, list):
            # 数组
            return getattr(self.column, attr_op)(self.value)
        elif isinstance(self.value, str):
            # 逗号分隔字符串
            value_list: t.List[str] = self.value.strip().split(",")
            return getattr(self.column, attr_op)(value_list)
        else:
            raise ParseError(f"{attr_op} 不支持的类型{self.value}:{type(self.value)}")


class LikeOpParser(SqlaOpParser):
    op_dict = {
        "like": "like",
        "ilike": "ilike",
        "notLike": "not_like",
        "notIlike": "not_ilike",
    }

    def parse(self):
        attr_op = self.op_dict[self.operate]
        value = self.value if str(self.value).count("%") else f"%{self.value}%"
        return getattr(self.column, attr_op)(value)


class OpParserFactory:
    parser_set: t.Set[t.Type[SqlaOpParser]] = {
        CmpOpParser, LikeOpParser, InOpParser
    }

    @classmethod
    def create(
        cls,
        column: InstrumentedAttribute,
        operate: str,
        value: t.Union[int, str, t.List[t.Any]],
    ) -> SqlaOpParser:
        for parser in cls.parser_set:
            if operate in parser.op_dict.keys():
                return parser(column, operate, value)
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
        if isinstance(model, (Alias, Annotated)):
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


def parse_suffix_operation(column: str, value: t.Union[int, str, t.List[t.Any]],
                           model: t.Type[Model]) -> t.Optional[SqlaExp]:
    if m := re.match(r"(?P<col>[\w\\.]+)_(?P<op>[\w]+)", column):
        col, op = m.group("col"), m.group("op")
        attr = parse_attribute_name(col, model)
    else:
        attr = parse_attribute_name(column, model)
        op = "in" if isinstance(value, list) else "eq"
    if attr is None:
        return None
    return OpParserFactory.create(attr, op, value).parse()


def parse_attribute_name(
        name: str,
        model: t.Type[Model]) -> t.Union[Column, InstrumentedAttribute]:
    """根据 model,name获取模型的字段对象.
    :param model: sqlalchemy.Model
    :param name: 字段名
    :return: 返回字段名对应的Column实例对象
    """
    if isinstance(model, (Alias, Table, Annotated)):
        attr = getattr(model.columns, udlcase(name), None)
    else:
        attr = getattr(model, udlcase(name), None)
    return attr


def parse_related_models(statement: Select) -> t.List[t.Union[Table, Alias]]:
    """获取Query对象查询涉及的所有表"""
    related_models: t.List[t.Union[Table, Alias]] = list()

    # 递归查找涉及表实体
    # 注意: 未包含子查询以及with语句涉及的表情况
    def recur_realted_models(_froms: t.List[t.Any],
                             related_models: t.List[t.Union[Table, Alias]]):
        for _from in _froms:
            if isinstance(_from, (Table, Alias)):
                # 表实体
                related_models.append(_from)
            elif isinstance(_from, _ORMJoin):
                # join实体
                recur_realted_models([_from.left, _from.right], related_models)
            elif isinstance(_from, Subquery):
                # 子查询
                recur_realted_models(_from.element.froms, related_models)
            else:
                raise TypeError(f"type:{_from} = {type(_from)}")

    recur_realted_models(_froms=statement.froms, related_models=related_models)
    return related_models
