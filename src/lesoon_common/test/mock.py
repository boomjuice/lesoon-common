from unittest import mock

from marshmallow.schema import Schema

from lesoon_common.dataclass.user import TokenUser


def mock_schema_dict_class():
    # mock schema的字典类
    return mock.patch.object(Schema, 'dict_class', dict)
