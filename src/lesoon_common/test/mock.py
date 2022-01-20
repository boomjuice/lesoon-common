from unittest import mock

from marshmallow.schema import Schema

from lesoon_common.dataclass.user import TokenUser


def mock_current_user():
    return mock.patch('lesoon_common.globals.get_current_user',
                      return_value=TokenUser.system_default())


def mock_schema_dict_class():
    # mock schema的字典类
    return mock.patch.object(Schema, 'dict_class', dict)
