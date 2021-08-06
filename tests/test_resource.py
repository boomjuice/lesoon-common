import pytest

from .api import api
from .api import bp
from .api import UserResource
from lesoon_common.utils.base import random_alpha_numeric


class TestLesoonResource:
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, app, db):
        api.register_resource(UserResource, "/User", endpoint="user")
        app.register_blueprint(bp)

    def test_register_resource(self, app):
        url_rule = app.url_map._rules
        rules = [_.rule for _ in url_rule]
        assert "/User" in rules
        assert "/User/<int:id>" in rules

    @staticmethod
    def generate_random_user(size: int):
        users = list()
        for i in range(size):
            user = {
                "id": i,
                "login_name": random_alpha_numeric(10),
                "user_name": random_alpha_numeric(10),
            }
            users.append(user)
        return users
