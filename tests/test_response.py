from lesoon_common.response import Response
from lesoon_common.response import ResponseCode
from lesoon_common.response import success_response


class TestResponseUtils:
    def test_success_response_null(self):
        expected_resp = Response(code=ResponseCode.Success)
        r = success_response()
        assert expected_resp.to_dict() == r

    def test_success_response_dict(self):
        result = {"a": 1}
        r = success_response(result=result)
        assert r["data"] == result

    def test_success_response_list(self):
        results = [{"a": 1}, {"b": 2}]
        r = success_response(result=results)
        assert r["rows"] == results

    def test_success_response_extra_type(self):
        result = "test"
        r = success_response(result=result)
        assert r["data"] == result
