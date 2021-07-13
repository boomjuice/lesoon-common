""" 通用Schema基类模块. """
import marshmallow.fields as ma_fields
from flask_sqlalchemy import Model
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy import SQLAlchemySchema

from ..extensions import db
from ..utils.base import camelcase


class FixedOperatorSchema:
    # 不准前端更新字段
    creator = ma_fields.Str(dump_only=True)
    modifier = ma_fields.Str(dump_only=True)
    create_time = ma_fields.DateTime(dump_only=True)
    modify_time = ma_fields.DateTime(dump_only=True)
    update_time = ma_fields.DateTime(dump_only=True)


class SqlaCamelSchema(SQLAlchemySchema, FixedOperatorSchema):
    # id字段只准序列化,不准反序列读取以防更新数据库id
    id = ma_fields.Str(dump_only=True)

    # 将序列化/反序列化的列名调整成驼峰命名
    def on_bind_field(self, field_name: str, field_obj: ma_fields.Field) -> None:
        field_obj.data_key = camelcase(field_obj.data_key or field_name)

    class Meta:
        model: Model = None
        # 如果load的键没有匹配到定义的field时的操作,
        # RAISE: 如果存在未知key,引发ValiadationError
        # EXCLUDE: 忽略未知key
        # INCLUDE: 包含未知可以,即使时未定义的field
        unknown = EXCLUDE
        sqla_session = db.session
        # 是否能通过实例对象序列化
        load_instance = True
        # 是否包含Model的关联关系
        include_relationships = False


class SqlaCamelAutoSchema(SqlaCamelSchema, SQLAlchemyAutoSchema):
    pass
