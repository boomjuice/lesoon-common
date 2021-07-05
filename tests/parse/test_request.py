from src.lesoon_core.parse.request import extract_sort_arg
from src.lesoon_core.parse.request import extract_where_arg
from src.lesoon_core.parse.request import parse_request
from src.lesoon_core.parse.request import ParsedRequest
from werkzeug.datastructures import ImmutableMultiDict


class TestReqParser:
    def test_parse_request_null(self):
        payload = ImmutableMultiDict([("test", 1)])
        req: ParsedRequest = parse_request(payload=payload)
        assert req.where is None
        assert req.sort is None
        assert req.page == 1
        assert req.page_size == 25

    def test_parse_request_invalid_page_args(self):
        payload = ImmutableMultiDict([("pageSize", 5000), ("page", -1)])
        req: ParsedRequest = parse_request(payload=payload)
        assert req.page == 1
        assert req.page_size == 1000

    def test_extract_sort_arg_str(self):
        sort = "created_at,-name"
        assert extract_sort_arg(sort) == [("created_at", 1), ("name", -1)]

    def test_extract_sort_arg_list(self):
        sort = '[("created_at",1), ("name", -1)]'
        assert extract_sort_arg(sort) == [("created_at", 1), ("name", -1)]

    def test_extract_sort_arg_null(self):
        sort = ""
        assert extract_sort_arg(sort) is None

    def test_extract_where_arg_dictionary(self):
        where = "{'id':1}"
        assert extract_where_arg(where) == {"id": 1}

    def test_extract_where_arg_null(self):
        where = ""
        assert extract_where_arg(where) is None
