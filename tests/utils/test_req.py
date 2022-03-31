import pytest

from lesoon_common.utils.req import convert_dict


class TestReq:

    def test_convert_dict(self):
        param = '{"id":1}'
        assert convert_dict(param) == {'id': 1}

        param = ''
        assert convert_dict(param) == {}

        param = '%7B%22a%22%3A%20%7B%22%24eq%22%3A%201%7D%7D'
        assert convert_dict(param) == {'a': {'$eq': 1}}

        param = 'orderNo asc'
        assert convert_dict(param, silent=True) == param
