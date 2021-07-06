from src.lesoon_core.parse.req import extract_sort_arg
from src.lesoon_core.parse.req import extract_where_arg


class TestReqParser:
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
