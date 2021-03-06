""" 通用Schema基类模块. """
import typing as t

import sqlalchemy as sa
from flask_sqlalchemy import Model
from marshmallow_sqlalchemy import ModelConverter
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import sqltypes

from lesoon_common.extensions import db
from lesoon_common.model.alchemy import fields
from lesoon_common.schema import BaseSchema
from lesoon_common.schema import CamelSchema


class SqlaModelConverter(ModelConverter):
    SQLA_TYPE_MAPPING = {
        sa.Enum: fields.Field,
        sa.JSON: fields.Raw,
        mysql.BIT: fields.Integer,
        mysql.YEAR: fields.Integer,
        mysql.SET: fields.List,
        mysql.ENUM: fields.Field,
        mysql.INTEGER: fields.Integer,
        mysql.DATETIME: fields.DateTime,
        mysql.BIGINT: fields.IntStr,
        sqltypes.DateTime: fields.DateTime,
        sqltypes.BigInteger: fields.IntStr,
        sqltypes.NullType: fields.Str
    }


class FixedOperatorSchema:
    # 不准前端更新字段
    creator = fields.Str(dump_only=True)
    modifier = fields.Str(dump_only=True)
    create_time = fields.DateTime(dump_only=True)
    modify_time = fields.DateTime(dump_only=True)
    update_time = fields.DateTime(dump_only=True)


class SqlaSchema(SQLAlchemySchema, BaseSchema, FixedOperatorSchema):
    # id字段只准序列化,不准反序列读取以防更新数据库id
    id = fields.IntStr(dump_only=True)

    def get_attribute(self, obj: t.Any, attr: str, default: t.Any):
        model_name = self.Meta.model.__name__
        if hasattr(obj, model_name) and hasattr(getattr(obj, model_name), attr):
            # 解决不使用别名进行关联查询的取值问题
            return super().get_attribute(getattr(obj, model_name), attr,
                                         default)
        else:
            return super().get_attribute(obj, attr, default)

    class Meta(BaseSchema.Meta):
        model: Model = None
        # sqlalchemy-session
        sqla_session = db.session
        # 是否能通过实例对象序列化
        load_instance: bool = True
        # 是否包含Model的关联关系
        include_relationships: bool = False
        # model字段映射类
        model_converter: t.Type[ModelConverter] = SqlaModelConverter


class SqlaAutoSchema(SqlaSchema, SQLAlchemyAutoSchema):
    pass


class SqlaCamelSchema(SqlaSchema, CamelSchema):
    pass


class SqlaCamelAutoSchema(SqlaCamelSchema, SQLAlchemyAutoSchema):
    pass
