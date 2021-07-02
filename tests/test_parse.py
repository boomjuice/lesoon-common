import pytest
from sqlalchemy.orm.util import aliased
from src.lesoon_core.exceptions import ParseError
from src.lesoon_core.parse.request import extract_sort_arg
from src.lesoon_core.parse.request import extract_where_arg
from src.lesoon_core.parse.sqlalchemy import parse_prefix_alias
from src.lesoon_core.parse.sqlalchemy import parse_sort
from src.lesoon_core.parse.sqlalchemy import parse_suffix_operation
from src.lesoon_core.parse.sqlalchemy import sqla_op


class TestReqParser:
    def test_extract_sort_arg_str(self):
        sort = "created_at,-name"
        assert extract_sort_arg(sort) == [["created_at"], ["name", -1]]

    def test_extract_sort_arg_list(self):
        sort = '[["created_at"], ["name", -1]]'
        assert extract_sort_arg(sort) == [["created_at"], ["name", -1]]

    def test_extract_sort_arg_null(self):
        sort = ""
        assert extract_sort_arg(sort) is None

    def test_extract_where_arg_dictionary(self):
        where = "{'id':1}"
        assert extract_where_arg(where) == {"id": 1}

    def test_extract_where_arg_null(self):
        where = ""
        assert extract_where_arg(where) is None


class TestSQLParser:
    """
    请求参数解析成sqlalchemy语法
    """

    def test_wrong_attribute(self, User):
        with pytest.raises(AttributeError):
            parse_suffix_operation("a", 1, User)

    def test_wrong_operation(self, User):
        with pytest.raises(ParseError):
            parse_suffix_operation("login_name_test", 1, User)

    def test_eq(self, User):
        expected_expression = sqla_op.eq(User.login_name, "john")
        r = parse_suffix_operation("login_name_eq", "john", User)
        assert expected_expression.compare(r) is True

    def test_gt(self, User):
        expected_expression = sqla_op.gt(User.status, 1)
        r = parse_suffix_operation("status_gt", 1, User)
        assert expected_expression.compare(r) is True

    def test_gte(self, User):
        expected_expression = sqla_op.ge(User.status, 1)
        r = parse_suffix_operation("status_gte", 1, User)
        assert expected_expression.compare(r) is True

    def test_lt(self, User):
        expected_expression = sqla_op.lt(User.status, 1)
        r = parse_suffix_operation("status_lt", 1, User)
        assert expected_expression.compare(r) is True

    def test_lte(self, User):
        expected_expression = sqla_op.le(User.status, 1)
        r = parse_suffix_operation("status_lte", 1, User)
        assert expected_expression.compare(r) is True

    def test_not_eq(self, User):
        expected_expression = sqla_op.ne(User.status, 1)
        r = parse_suffix_operation("status_ne", 1, User)
        assert expected_expression.compare(r) is True

    def test_like(self, User):
        expected_expression = User.status.like("%1%")
        r = parse_suffix_operation("status_like", "%1%", User)
        assert expected_expression.compare(r) is True

    def test_in(self, User):
        expected_expression = User.status.in_(["1", "2", "3"])
        r = parse_suffix_operation("status_in", "1,2,3", User)
        assert expected_expression.compare(r) is True

    def test_parse_alias_match(self, User):
        a = aliased(User, name="a")
        r = parse_prefix_alias(a, "a.id")
        assert r == "id"

    def test_parse_alias_not_match(self, User):
        a = aliased(User, name="a")
        r = parse_prefix_alias(a, "b.id")
        assert r is None

    def test_parse_alias_invalid_col(self, User):
        with pytest.raises(ParseError):
            a = aliased(User, name="a")
            parse_prefix_alias(a, "a.b.c")

    def test_parse_sort_null(self, User):
        assert parse_sort([], User) == []

    def test_parse_sort_standard(self, User):
        sort_list = [["id"], ["status", -1]]
        expected_expression = [User.id, User.status.desc()]
        r = parse_sort(sort_list, User)
        # 字段无compare函数
        assert expected_expression[0] is r[0]
        assert expected_expression[1].compare(r[1])
