""" 额外类库封装模块. """
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from flask import current_app
from flask import make_response
from flask import render_template_string
from flask import request
from flask.wrappers import Request
from flask_debugtoolbar import DebugToolbarExtension
from flask_jwt_extended import current_user
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import BaseQuery
from jose import jwe
from jose.exceptions import JWEError
from werkzeug.utils import cached_property

from .parse.req import extract_sort_arg
from .parse.req import extract_where_arg
from .parse.sqla import parse_multi_condition
from .parse.sqla import parse_related_models
from .utils.jwt import load_user_from_token


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

    @cached_property
    def user(self):
        return current_user


class LesoonQuery(BaseQuery):
    def paginate(self, page=None, per_page=None, error_out=True, max_per_page=None):
        """禁用分页异常以及限制最大分页数"""
        page = page or request.page
        per_page = per_page or request.page_size
        return super().paginate(page, per_page, False, 1000)

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


class LesoonJwt(JWTManager):
    def __init__(self, app=None):
        super().__init__(app=app)
        # flask_jwt_extended.current_user()的取值函数
        self._user_lookup_callback = load_user_from_token

    def _encode_jwt_from_config(
        self,
        identity,
        token_type,
        claims=None,
        fresh=False,
        expires_delta=None,
        headers=None,
    ):
        jwt_token = super()._encode_jwt_from_config(
            identity, token_type, claims, fresh, expires_delta, headers
        )
        secret = current_app.config.get("JWT_SECRET_KEY")
        return jwe.encrypt(jwt_token, key=secret, cty="JWT")

    def _decode_jwt_from_config(
        self, encoded_token, csrf_value=None, allow_expired=False
    ):
        try:
            secret = current_app.config.get("JWT_SECRET_KEY")
            encoded_token = jwe.decrypt(jwe_str=encoded_token, key=secret).decode()
        except JWEError:
            pass
        return super()._decode_jwt_from_config(encoded_token, csrf_value, allow_expired)


class LesoonDebugTool(DebugToolbarExtension):
    def init_app(self, app):
        wrap_json = """
        <html>
            <head>
                <title>Debugging JSON Response</title>
            </head>

            <body>
                <h1>Wrapped JSON Response</h1>

                <h2>HTTP Code</h2>
                <pre>{{ http_code }}</pre>

                <h2>JSON Response</h2>
                <pre>{{ response }}</pre>
            </body>
        </html>
        """

        def json_to_html(response):
            if response.mimetype == "application/json" and request.args.get("_debug"):
                html_wrapped_response = make_response(
                    render_template_string(
                        wrap_json,
                        response=response.data.decode("utf-8"),
                        http_code=response.status,
                    ),
                    response.status_code,
                )
                return app.process_response(html_wrapped_response)

            return response

        app.after_request(json_to_html)
        super().init_app(app)
