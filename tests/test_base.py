import pytest
from werkzeug.exceptions import MethodNotAllowed

from .api import api
from .api import bp
from .api import UserResource
from lesoon_common.base import handle_exception
from lesoon_common.base import LesoonFlask
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
        r = Response.load(handle_exception(AttributeError("test")))
        assert r.code == str(ResponseCode.Error.code)

    def test_handle_service_exception(self, app):
        r = handle_exception(ServiceError(code=ResponseCode.Success, msg="test"))
        r = Response.load(r)
        assert r.code == str(ResponseCode.Success.code)
        assert r.msg == "test"


class TestLesoonFlask:
    def test_init_default_extensions(self):
        app = LesoonFlask(__name__)
        assert app.registered_extensions is LesoonFlask.default_extensions
        for name, ext in LesoonFlask.default_extensions.items():
            assert getattr(app, name) is ext

    def test_init_custom_extensions(self, app):
        mock = ExtMock()
        app = LesoonFlask(__name__, extra_extensions={"test": mock})
        assert app.registered_extensions["test"] is mock
        assert mock.init is True
        assert getattr(app, "test") is mock  # noqa:B009


class TestLesoonApi:
    @pytest.fixture(autouse=True)
    def setup_method(self, app):
        api.register_resource(UserResource, "/User", endpoint="user")
        app.register_blueprint(bp)

    def test_register_resource(self, app):
        url_rule = app.url_map._rules
        rules = [_.rule for _ in url_rule]
        assert "/User" in rules
        assert "/User/<int:id>" in rules
