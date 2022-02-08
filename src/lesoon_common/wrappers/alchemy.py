""" sqlalchemy自定义封装模块. """
import typing as t

from flask_sqlalchemy import BaseQuery
from flask_sqlalchemy import Pagination

from lesoon_common.globals import request
from lesoon_common.parse.sqla import parse_multi_condition
from lesoon_common.parse.sqla import parse_related_models


class LesoonQuery(BaseQuery):

    def paginate(
        self,
        if_page: t.Optional[bool] = None,
        page: t.Optional[int] = None,
        per_page: t.Optional[int] = None,
        count_query: t.Optional[BaseQuery] = None,
    ):
        """
        执行分页查询.

        Args:
            if_page: 是否分页
            page: 页码
            per_page: 页大小
            count_query: 总计查询对象,默认为self.count()

        """
        page = page or request.page  # type:ignore
        per_page = per_page or request.page_size  # type:ignore
        if_page = if_page or request.if_page  # type:ignore
        count_query = count_query or self

        if if_page:
            items = self.limit(per_page).offset((page - 1) * per_page).all()
        else:
            items = self.all()
        total = count_query.order_by(None).count()

        return Pagination(self, page, per_page, total, items)

    def with_request_condition(self,
                               add_where: bool = True,
                               add_sort: bool = True):
        """注入请求查询过滤条件.
        : 将请求参数转化成sqlalchemy语法,注入Query对象
        : 注意 此方法只能在Flask请求上下文中调用
        """
        if any([add_where, add_sort]):
            related_models = parse_related_models(self.statement)
            where_list, sort_list = parse_multi_condition(
                request.where.copy(),  # type:ignore
                request.sort.copy(),  # type:ignore
                related_models,
            )
            if add_where:
                self = self.filter(*where_list)  # noqa
            if add_sort:
                self = self.order_by(*sort_list)  # noqa
        return self
