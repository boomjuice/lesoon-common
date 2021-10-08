import typing

from marshmallow.fields import AwareDateTime
from marshmallow.fields import Bool
from marshmallow.fields import Boolean
from marshmallow.fields import Constant
from marshmallow.fields import Date
from marshmallow.fields import DateTime
from marshmallow.fields import Decimal
from marshmallow.fields import Dict
from marshmallow.fields import Email
from marshmallow.fields import Field
from marshmallow.fields import Float
from marshmallow.fields import Function
from marshmallow.fields import Int
from marshmallow.fields import Integer
from marshmallow.fields import IP
from marshmallow.fields import IPInterface
from marshmallow.fields import IPv4
from marshmallow.fields import IPv4Interface
from marshmallow.fields import IPv6
from marshmallow.fields import IPv6Interface
from marshmallow.fields import List
from marshmallow.fields import Mapping
from marshmallow.fields import Method
from marshmallow.fields import NaiveDateTime
from marshmallow.fields import Nested
from marshmallow.fields import Number
from marshmallow.fields import Pluck
from marshmallow.fields import Raw
from marshmallow.fields import Str
from marshmallow.fields import String
from marshmallow.fields import Time
from marshmallow.fields import TimeDelta
from marshmallow.fields import Tuple
from marshmallow.fields import URL
from marshmallow.fields import Url
from marshmallow.fields import UUID


class IntStr(Integer, String):
    default_error_messages = {"invalid": "Not a valid integer."}

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any,
                   **kwargs):
        return String._serialize(self, value, attr, obj, **kwargs)

    def _deserialize(self, value: typing.Any, attr: typing.Optional[str],
                     data: typing.Optional[typing.Mapping[str, typing.Any]],
                     **kwargs):
        return Integer._deserialize(self, value, attr, data, **kwargs)
