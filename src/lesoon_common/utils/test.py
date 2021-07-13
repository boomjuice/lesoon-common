""" 单元测试基类. """


class TestMixin:
    def assertEqual(self, left, right):
        assert left == right

    def assertTrue(self, value):
        assert value is True

    def assertNone(self, value):
        assert value is None

    def assertList(self, value):
        assert isinstance(value, list)

    def assertDict(self, value):
        assert isinstance(value, dict)

    def assertType(self, value, v_type):
        assert type(value) == v_type

    def assertLen(self, value, length: int):
        assert len(value) == length
