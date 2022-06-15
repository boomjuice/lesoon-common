import typing as t
from dataclasses import field
from functools import partial

from marshmallow import Schema
from marshmallow_dataclass import dataclass as _dataclass

from lesoon_common.schema import CamelSchema

# 覆盖生成的Schema基类为CamelSchema
dataclass = partial(_dataclass, base_schema=CamelSchema)  # type:ignore


@dataclass
class BaseDataClass:
    Schema: t.ClassVar[t.Type[Schema]] = Schema

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def load(cls, data, **kwargs):
        return cls.Schema().load(data, **kwargs)

    @classmethod
    def dump(cls, data, **kwargs):
        return cls.Schema().dump(data, **kwargs)

    def json(self, **kwargs):
        return self.Schema().dump(self, **kwargs)
