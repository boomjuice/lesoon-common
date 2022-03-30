import pytest
from sqlalchemy.exc import DatabaseError
from tests.conftest import Config
from werkzeug.exceptions import MethodNotAllowed

from lesoon_common.base import handle_exception
from lesoon_common.base import LesoonFlask
from lesoon_common.code import MysqlCode
from lesoon_common.exceptions import ServiceError
from lesoon_common.response import Response
from lesoon_common.response import ResponseCode


class ExtMock:

    def __init__(self):
        self.init = False

    def init_app(self, app):
        self.init = True


class TestAppHandler:

    def test_handle_http_exception(self, app):
        expected_error = MethodNotAllowed()
        r = handle_exception(expected_error)
        assert r == expected_error

    def test_handle_inter_exception(self, app):
        r = Response.load(handle_exception(AttributeError('test')))
        assert r.code == str(ResponseCode.Error.code)

    def test_handle_service_exception(self, app):
        r = handle_exception(ServiceError(code=ResponseCode.Success,
                                          msg='test'))
        r = Response.load(r)
        assert r.code == str(ResponseCode.Success.code)
        assert r.msg == 'test'

    def test_handle_call_exception(self, app):

        class RemoteCallError:
            pass

        error = RemoteCallError()
        error.code = ResponseCode.RemoteCallError.code
        error.msg = ResponseCode.RemoteCallError.msg
        r = handle_exception(error)
        r = Response.load(r)
        assert r.code == str(ResponseCode.RemoteCallError.code)
        assert r.msg == '远程调用异常'

    def test_handle_database_exception(self, app):
        from MySQLdb._exceptions import IntegrityError
        r = handle_exception(
            DatabaseError(
                orig=IntegrityError(
                    MysqlCode.DUP_ENTRY.code,
                    "Duplicate entry '1231241324-123' for key 'uk_sys_user_role'"
                ),
                params=(1, None, '超级管理员', None, None, 1231241324, 123),
                statement=
                'INSERT INTO sys_user_role (company_id, remarks, creator, modifier'
                ', modify_time, user_id, role_id) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)'))
        r = Response.load(r)
        assert r.code == ResponseCode.DataBaseError.code
        assert r.msg == MysqlCode.DUP_ENTRY.msg


class TestLesoonFlask:

    def test_init_default_extensions(self):
        app = LesoonFlask(__name__, config=Config)
        assert app.registered_extensions is LesoonFlask.default_extensions
        for name, ext in LesoonFlask.default_extensions.items():
            assert getattr(app, name) is ext

    def test_init_custom_extensions(self, app):
        mock = ExtMock()
        app = LesoonFlask(__name__,
                          config=Config,
                          extra_extensions={'test': mock})
        assert app.registered_extensions['test'] is mock
        assert mock.init is True
        assert getattr(app, 'test') is mock  # noqa:B009
