import typing as t
from functools import partial

from marshmallow import Schema
from marshmallow_dataclass import dataclass

from lesoon_common.model.schema import CamelSchema

# 覆盖生成的Schema基类为CamelSchema
dataclass = partial(dataclass, base_schema=CamelSchema)


@dataclass
class BaseDataClass:
    Schema: t.ClassVar[t.Type[Schema]] = Schema

    @classmethod
    def load(cls, data, **kwargs):
        return cls.Schema().load(data, **kwargs)

    @classmethod
    def dump(cls, data, **kwargs):
        return cls.Schema().dump(data, **kwargs)
