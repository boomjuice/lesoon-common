from src.lesoon_core.response import error_response
from src.lesoon_core.response import handle_exception
from src.lesoon_core.response import Response
from src.lesoon_core.response import ResponseCode
from src.lesoon_core.response import success_response
from werkzeug.exceptions import MethodNotAllowed


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

    def test_error_response_null(self):
        r = error_response(None)
        assert r["code"] == ResponseCode.Error.code

    def test_handle_http_exception(self, app):
        expected_error = MethodNotAllowed()
        r = handle_exception(expected_error)
        assert r == expected_error

    def test_handle_inter_exception(self, app):
        r = handle_exception(AttributeError("test"))
        assert isinstance(r, dict) is True
        assert r["code"] == ResponseCode.Error.code
