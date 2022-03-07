from unittest import mock

from marshmallow_sqlalchemy.schema import SQLAlchemySchemaMeta

from lesoon_common.model.alchemy.schema import SqlaSchema


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
