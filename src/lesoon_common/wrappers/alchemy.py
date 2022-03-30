""" sqlalchemy自定义封装模块. """
import typing as t

from flask_sqlalchemy import BaseQuery
from flask_sqlalchemy import Pagination

from lesoon_common.globals import request


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
