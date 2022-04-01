import typing as t
from dataclasses import field

import marshmallow as ma

from lesoon_common.dataclass.base import BaseDataClass
from lesoon_common.dataclass.base import dataclass


@dataclass
class Flag(BaseDataClass):
    ret_code: str
    ret_msg: str
    ret_detail: str
    solution: t.Optional[str] = None


@dataclass
class Response(BaseDataClass):
    flag: Flag = field(
        metadata={'marshmallow_field': ma.fields.Nested(Flag.Schema)})
    data: t.Optional[dict] = None
    rows: t.Optional[t.List[dict]] = None
