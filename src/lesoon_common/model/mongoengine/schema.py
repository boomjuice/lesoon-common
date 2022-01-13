""" 通用Schema基类模块. """
from flask_mongoengine import Document
from marshmallow import EXCLUDE
from marshmallow_mongoengine import ModelSchema

from lesoon_common.model.mongoengine import fields


class FixedOperatorSchema:
    # 不准前端更新字段
    creator = fields.Str(dump_only=True)
    modifier = fields.Str(dump_only=True)
    create_time = fields.DateTime(dump_only=True)
    modify_time = fields.DateTime(dump_only=True)


class MongoAutoSchema(ModelSchema, FixedOperatorSchema):

    def load(self, data, *, instance=None, **kwargs):
        if instance:
            return self.update(obj=instance, data=data)
        else:
            return super().load(data, **kwargs)

    class Meta:
        # 如果load的键没有匹配到定义的field时的操作
        # RAISE: 如果存在未知key,引发ValidationError
        # EXCLUDE: 忽略未知key
        # INCLUDE: 包含未知可以,即使时未定义的field
        unknown: str = EXCLUDE
        # 排除字段
        exclude: list = []
        # 保持有序
        ordered = True
        # 时间格式
        datetimeformat = '%Y-%m-%d %H:%M:%S'
        # sqlalchemy-model
        model: Document = None
        # 是否能通过实例对象序列化
        model_build_obj: bool = True
        # 是否主键只允许序列化
        model_dump_only_pk: bool = True
