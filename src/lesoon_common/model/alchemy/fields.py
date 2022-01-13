import typing

from marshmallow.fields import *  # noqa


class IntStr(Integer, String):
    default_error_messages = {'invalid': 'Not a valid integer.'}

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any,
                   **kwargs):
        return String._serialize(self, value, attr, obj, **kwargs)

    def _deserialize(self, value: typing.Any, attr: typing.Optional[str],
                     data: typing.Optional[typing.Mapping[str, typing.Any]],
                     **kwargs):
        return Integer._deserialize(self, value, attr, data, **kwargs)
