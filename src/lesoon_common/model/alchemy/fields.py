import typing

import marshmallow as ma
from marshmallow.fields import *  # noqa
from marshmallow.utils import _iso8601_date_re as date_re  # noqa
from marshmallow_sqlalchemy.fields import Nested
from marshmallow_sqlalchemy.fields import Related
from marshmallow_sqlalchemy.fields import RelatedList


class IntStr(ma.fields.Int, ma.fields.Str):
    default_error_messages = {'invalid': 'Not a valid integer.'}

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any,
                   **kwargs):
        return String._serialize(self, value, attr, obj, **kwargs)

    def _deserialize(self, value: typing.Any, attr: typing.Optional[str],
                     data: typing.Optional[typing.Mapping[str, typing.Any]],
                     **kwargs):
        return Integer._deserialize(self, value, attr, data, **kwargs)


class DateTime(ma.fields.DateTime):

    def _deserialize(self, value: typing.Any, attr: typing.Optional[str],
                     data: typing.Optional[typing.Mapping[str, typing.Any]],
                     **kwargs):
        if date := date_re.match(value):
            value = f'{date.group()} 00:00:00'
        return super()._deserialize(value, attr, data, **kwargs)
