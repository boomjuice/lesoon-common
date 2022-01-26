""" 通用Schema基类模块. """
from flask_mongoengine import Document
from marshmallow_mongoengine import ModelSchema

from lesoon_common.model.mongoengine import fields
from lesoon_common.schema import BaseSchema
from lesoon_common.schema import CamelSchema


class FixedOperatorSchema:
    # 不准前端更新字段
    creator = fields.Str(dump_only=True)
    modifier = fields.Str(dump_only=True)
    create_time = fields.DateTime(dump_only=True)
    modify_time = fields.DateTime(dump_only=True)


class MongoAutoSchema(ModelSchema, BaseSchema, FixedOperatorSchema):

    def load(self, data, *, instance=None, **kwargs):
        if instance:
            return self.update(obj=instance, data=data)
        else:
            return super().load(data, **kwargs)

    class Meta(BaseSchema.Meta):
        # mongo-document
        model: Document = None
        # 是否能通过实例对象序列化
        model_build_obj: bool = True
        # 是否主键只允许序列化
        model_dump_only_pk: bool = True


class MongoCamelAutoSchema(MongoAutoSchema, CamelSchema):
    pass
