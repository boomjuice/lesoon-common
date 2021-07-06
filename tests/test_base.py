from flask_restful import Resource
from src.lesoon_core.base import LesoonFlask


class ExtMock:
    def __init__(self):
        self.init = False

    def init_app(self, app):
        self.init = True


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
        assert getattr(app, "test") is mock


class TestLesoonApi:
    def test_register_resource(self):
        class TestResource(Resource):
            pass
