import pytest


class TestResource:
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, app, db):
        pass

    def test_resource_url_rule(self, app):
        print(app.url_map)
        assert 1
