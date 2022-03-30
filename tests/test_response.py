from collections import OrderedDict

from lesoon_common.response import ClientResponse
from lesoon_common.response import Response
from lesoon_common.response import ResponseBase
from lesoon_common.response import ResponseCode


class TestResponseABC:

    def test_load(self):
        resp_dict = {
            'flag': {
                'retCode': '1234',
                'retMsg': 'test'
            },
            'total': 1,
        }
        resp = ResponseBase.load(resp_dict)
        assert resp.code == '1234'
        assert resp.total == 1

    def test_none(self):
        expected_resp = Response(code=ResponseCode.Success)
        assert expected_resp.to_dict() == Response.success()

    def test_fixed_attr(self):
        r = Response.success(total=123)
        assert r['total'] == 123

    def test_custom_attr(self):
        r = Response.success(test=123)
        assert r['test'] == 123


class TestResponse:

    def test_load(self):
        resp_dict = {
            'flag': {
                'retCode': '1234',
                'retMsg': 'test'
            },
            'data': {
                'a': 1
            },
            'total': 1,
        }
        resp = Response.load(resp_dict)
        assert resp.code == '1234'
        assert resp.result == {'a': 1}
        assert resp.total == 1

        resp_dict = {
            'flag': {
                'retCode': '1234',
                'retMsg': 'test'
            },
            'rows': [{
                'a': 1
            }],
            'total': 1,
        }
        resp = Response.load(resp_dict)
        assert resp.code == '1234'
        assert resp.result == [{'a': 1}]
        assert resp.total == 1

    def test_mapping_result(self):
        result = {'a': 1}
        r = Response.success(result=result)
        assert r['data'] == result

        result = OrderedDict({'a': 1})
        r = Response.success(result=result)
        assert r['data'] == result

    def test_sequence_result(self):
        results = [{'a': 1}, {'b': 2}]
        r = Response.success(result=results)
        assert r['rows'] == results

        results = ({'a': 1}, {'b': 2})
        r = Response.success(result=results)
        assert r['rows'] == list(results)

        results = {'a', 'b', 'c'}
        r = Response.success(result=results)
        assert r['rows'] == list(results)

    def test_unknown_type(self):
        result = 'test'
        r = Response.success(result=result)
        assert r['data'] == result


class TestClientResponse:

    def test_load(self):
        resp_dict = {
            'flag': {
                'retCode': '1234',
                'retMsg': 'test'
            },
            'body': {
                'a': 1
            },
            'total': 1,
        }
        resp = ClientResponse.load(resp_dict)
        assert resp.code == '1234'
        assert resp.result == {'a': 1}
        assert resp.total == 1

    def test_result(self):
        result = {'a': 1}
        r = ClientResponse.success(result=result)
        assert r['body'] == result
