import pytest

from lesoon_common.utils.str import camelcase
from lesoon_common.utils.str import udlcase


class TestStrUtil:

    def test_camelcase_empty(self):
        assert camelcase("") == ""

    def test_camelcase_udl(self):
        assert camelcase("test_example") == "testExample"

    def test_camelcase_invalid(self):
        with pytest.raises(TypeError):
            camelcase(111)

    def test_udlcase_empty(self):
        assert udlcase("") == ""

    def test_udlcase_camel(self):
        assert udlcase("testExample") == "test_example"

    def test_udlcase_invalid(self):
        with pytest.raises(TypeError):
            udlcase(111)
