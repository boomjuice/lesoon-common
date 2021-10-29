import pytest
from sqlalchemy.sql.expression import alias
from tests.models import User
from tests.models import UserExt

from lesoon_common.exceptions import ParseError
from lesoon_common.parse.sqla import parse_filter
from lesoon_common.parse.sqla import parse_prefix_alias
from lesoon_common.parse.sqla import parse_related_models
from lesoon_common.parse.sqla import parse_sort
from lesoon_common.parse.sqla import parse_suffix_operation
from lesoon_common.parse.sqla import sqla_op


class TestSQLParser:
    """
    请求参数解析成sqlalchemy语法
    """

    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, db):
        pass

    def test_wrong_attribute(self):
        assert parse_suffix_operation('a', '1', User) is None

    def test_wrong_operation(self):
        with pytest.raises(ParseError):
            parse_suffix_operation('login_name_test', '1', User)

    def test_operation_no_suffix(self):
        expected_expression = sqla_op.eq(User.status, '1')
        r = parse_suffix_operation('status', '1', User)
        assert expected_expression.compare(r) is True

    def test_operation_eq(self):
        expected_expression = sqla_op.eq(User.login_name, 'john')
        r = parse_suffix_operation('login_name_eq', 'john', User)
        assert expected_expression.compare(r) is True

    def test_operation_gt(self):
        expected_expression = sqla_op.gt(User.status, 1)
        r = parse_suffix_operation('status_gt', 1, User)
        assert expected_expression.compare(r) is True

    def test_operation_gte(self):
        expected_expression = sqla_op.ge(User.status, 1)
        r = parse_suffix_operation('status_gte', 1, User)
        assert expected_expression.compare(r) is True

    def test_operation_lt(self):
        expected_expression = sqla_op.lt(User.status, 1)
        r = parse_suffix_operation('status_lt', 1, User)
        assert expected_expression.compare(r) is True

    def test_operation_lte(self):
        expected_expression = sqla_op.le(User.status, 1)
        r = parse_suffix_operation('status_lte', 1, User)
        assert expected_expression.compare(r) is True

    def test_operation_not_eq(self):
        expected_expression = sqla_op.ne(User.status, 1)
        r = parse_suffix_operation('status_ne', 1, User)
        assert expected_expression.compare(r) is True

    def test_operation_like_normal(self):
        expected_expression = User.status.like('%1%')
        r = parse_suffix_operation('status_like', '1', User)
        assert expected_expression.compare(r) is True

    def test_operation_like(self):
        expected_expression = User.status.like('%1')
        r = parse_suffix_operation('status_like', '%1', User)
        assert expected_expression.compare(r) is True

    def test_operation_not_like(self):
        expected_expression = User.status.not_like('%1')
        r = parse_suffix_operation('status_notLike', '%1', User)
        assert expected_expression.compare(r) is True

    def test_operation_in(self):
        expected_expression = User.status.in_(['1', '2', '3'])
        r = parse_suffix_operation('status_in', '1,2,3', User)
        assert expected_expression.compare(r) is True

    def test_operation_notin(self):
        expected_expression = User.status.notin_(['1', '2', '3'])
        r = parse_suffix_operation('status_notIn', '1,2,3', User)
        assert expected_expression.compare(r) is True

    def test_filter_null(self):
        r = parse_filter({}, User)
        assert type(r) == list
        assert len(r) == 0

    def test_parse_alias_match(self):
        a = alias(User, name='a')
        r = parse_prefix_alias('a.id', a)
        assert r == 'id'

    def test_parse_alias_not_match(self):
        a = alias(User, name='a')
        r = parse_prefix_alias('b.id', a)
        assert r is None

    def test_parse_alias_invalid_col(self):
        with pytest.raises(ParseError):
            a = alias(User, name='a')
            parse_prefix_alias('a.b.c', a)

    def test_parse_sort_null(self):
        assert parse_sort([], User) == []

    def test_parse_sort_standard(self):
        sort_list = [('id',), ('status', 'desc')]
        expected_expression = [User.id, User.status.desc()]
        r = parse_sort(sort_list, User)
        # 字段无compare函数
        assert expected_expression[0] is r[0]
        assert expected_expression[1].compare(r[1])

    def test_parse_related_models_single(self):
        query = User.query
        r = parse_related_models(statement=query.statement)
        assert len(r) == 1
        assert r.pop() == User.__table__

    def test_parse_related_models_join(self):
        query = User.query.join(UserExt, User.id == UserExt.user_id)
        r = parse_related_models(statement=query.statement)
        assert len(r) == 2
        assert r == [User.__table__, UserExt.__table__]
