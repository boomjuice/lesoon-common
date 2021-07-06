""" 额外类库封装模块. """
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from flask import Request
from flask import request
from flask_sqlalchemy import BaseQuery
from werkzeug.utils import cached_property

from .parse.req import extract_sort_arg
from .parse.req import extract_where_arg
from .parse.sqla import parse_multi_condition
from .parse.sqla import parse_related_models


class LesoonRequest(Request):
    PAGE_SIZE_DEFAULT = 25
    PAGE_SIZE_LIMIT = 1000

    @cached_property
    def where(self) -> Optional[Dict[str, str]]:
        where = extract_where_arg(self.args.get("where"))
        return where

    @cached_property
    def sort(self) -> Optional[List[Tuple[str, int]]]:
        sort = extract_sort_arg(self.args.get("sort"))
        return sort

    @cached_property
    def page(self) -> int:
        page = self.args.get("page", default=1, type=int)
        return page  # type:ignore

    @cached_property
    def page_size(self) -> int:
        page_size = self.args.get(
            "pageSize", default=self.__class__.PAGE_SIZE_DEFAULT, type=int
        )
        if page_size > self.__class__.PAGE_SIZE_LIMIT:  # type:ignore
            page_size = self.__class__.PAGE_SIZE_LIMIT
        return page_size  # type:ignore


class LesoonQuery(BaseQuery):
    def with_request_condition(self, add_where: bool = True, add_sort: bool = True):
        """注入请求查询过滤条件.
        : 将请求参数转化成sqlalchemy语法,注入Query对象
        : 注意 此方法依赖于Flask请求上下文
        """
        if any([add_where, add_sort]):
            related_models = parse_related_models(self)
            where_list, sort_list = parse_multi_condition(
                request.where,  # type:ignore
                request.sort,  # type:ignore
                related_models,
            )
            if add_where:
                self = self.filter(*where_list)
            if add_sort:
                self = self.order_by(*sort_list)
        return self
