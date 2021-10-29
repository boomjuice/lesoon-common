from lesoon_common.response import error_response
from lesoon_common.response import Response
from lesoon_common.response import ResponseCode
from lesoon_common.response import success_response


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
        assert resp.data == {'a': 1}
        assert resp.total == 1


class TestResponseUtils:

    def test_success_response_null(self):
        expected_resp = Response(code=ResponseCode.Success)
        r = success_response()
        assert expected_resp.to_dict() == r

    def test_success_response_dict(self):
        result = {'a': 1}
        r = success_response(result=result)
        assert r['data'] == result

    def test_success_response_list(self):
        results = [{'a': 1}, {'b': 2}]
        r = success_response(result=results)
        assert r['rows'] == results

    def test_success_response_extra_type(self):
        result = 'test'
        r = success_response(result=result)
        assert r['data'] == result

    def test_success_response_custom_key(self):
        r = success_response(total=123)
        assert r['total'] == 123

    def test_error_response_null(self):
        r = Response.load(error_response())
        assert r.code == str(ResponseCode.Error.code)
