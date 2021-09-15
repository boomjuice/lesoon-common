from lesoon_common.parse.req import extract_sort_arg
from lesoon_common.parse.req import extract_where_arg


class TestReqParser:
    def test_extract_sort_arg_str(self):
        sort = "created_at,-name"
        assert extract_sort_arg(sort) == [("created_at", 1), ("name", -1)]

    def test_extract_sort_arg_list(self):
        sort = '[["created_at",1], ["name", -1]]'
        assert extract_sort_arg(sort) == [["created_at", 1], ["name", -1]]

    def test_extract_sort_arg_null(self):
        sort = ""
        assert extract_sort_arg(sort) == []

    def test_extract_where_arg_dictionary(self):
        where = '{"id":1}'
        assert extract_where_arg(where) == {"id": 1}

    def test_extract_where_arg_null(self):
        where = ""
        assert extract_where_arg(where) == {}

    def test_extract_where_special_char(self):
        where = "%7B%22loginName_like%22:%22a%22%7D"
        assert extract_where_arg(where) == {"loginName_like": "a"}
