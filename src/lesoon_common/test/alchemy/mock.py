from unittest import mock

from marshmallow_sqlalchemy.schema import SQLAlchemySchemaMeta

from lesoon_common.code import ResponseCode
from lesoon_common.model.alchemy.schema import SqlaSchema
from lesoon_common.utils.base import generate_id


class UnittestSQLAlchemySchemaMeta(SQLAlchemySchemaMeta):

    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        fields = super().get_declared_fields(klass, cls_fields,
                                             inherited_fields, dict_cls)
        for k, f in fields.items():
            if k not in ('modifier', 'modify_time'):
                f.dump_only = False
        return fields


class UnittestSqlaSchema(SqlaSchema, metaclass=UnittestSQLAlchemySchemaMeta):

    class Meta(SqlaSchema.Meta):
        pass


def mock_alchemy_schema():
    return mock.patch('lesoon_common.model.alchemy.schema.SqlaSchema',
                      UnittestSqlaSchema)


def mock_get_distribute_id():
    from lesoon_client import IdCenterClient

    def mock_id(self):
        response = mock.Mock(code=ResponseCode.Success.code,
                             result=generate_id())
        return response

    return mock.patch.object(IdCenterClient, 'get_uid', mock_id)
