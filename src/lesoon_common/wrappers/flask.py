import typing as t
from datetime import datetime
from decimal import Decimal

from flask import Flask
from flask.ctx import has_request_context
from flask.globals import request
from flask.helpers import make_response
from flask.json import JSONEncoder
from flask.templating import render_template_string
from flask.testing import FlaskClient
from flask.wrappers import Request
from flask.wrappers import Response as FlaskResponse
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import cached_property

from lesoon_common.code.response import ResponseCode
from lesoon_common.exceptions import ServiceError
from lesoon_common.globals import current_user
from lesoon_common.response import Response
from lesoon_common.response import ResponseBase
from lesoon_common.utils.jwt import get_token
from lesoon_common.utils.str import camelcase

ResponseType = t.Union[ResponseBase, FlaskResponse]


class LesoonRequest(Request):
    PAGE_SIZE_DEFAULT = 25
    PAGE_SIZE_LIMIT = 100000

    @cached_property
    def where(self) -> t.Optional[str]:
        where = self.args.get('where')
        return where

    @cached_property
    def sort(self) -> t.Optional[str]:
        sort = self.args.get('sort')
        return sort

    @cached_property
    def if_page(self) -> bool:
        if_page = bool(self.args.get('ifPage', default=1, type=int))
        return if_page

    @cached_property
    def page(self):
        page = self.args.get('page', type=int)
        if not page:
            # TODO: Java导入导出中心旧分页参数适配
            page = self.args.get('page.pn', default=1, type=int)
        if page < 1:
            page = 1
        return page

    @cached_property
    def page_size(self):
        page_size = self.args.get('pageSize', type=int)
        if not page_size:
            # TODO: Java导入导出中心旧分页参数适配
            page_size = self.args.get('page.size',
                                      default=self.__class__.PAGE_SIZE_DEFAULT,
                                      type=int)

        if page_size < 0:
            page_size = self.__class__.PAGE_SIZE_DEFAULT

        if page_size > self.__class__.PAGE_SIZE_LIMIT:  # type:ignore
            page_size = self.__class__.PAGE_SIZE_LIMIT
        return page_size  # type:ignore

    @cached_property
    def user(self):
        return current_user

    @cached_property
    def token(self) -> str:
        if has_request_context():
            return get_token()
        else:
            return ''


class LesoonTestClient(FlaskClient):

    def __init__(self,
                 *args: t.Any,
                 camel: bool = False,
                 convert_object: bool = True,
                 load_response: bool = True,
                 datetime_format: str = '%Y-%m-%d %H:%M:%S',
                 response_cls: t.Type[ResponseBase] = Response,
                 **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.camel = camel
        self.convert_object = convert_object
        self.datetime_format = datetime_format
        self.load_response = load_response
        self.response_cls = response_cls

    def _camelcase_key(self, data: t.Mapping):
        return {camelcase(k): v for k, v in data.items()}

    def _convert_datetime(self, data: t.Mapping):
        new_data = {}
        for k, v in data.items():
            if isinstance(v, datetime):
                v = v.strftime(self.datetime_format)
            new_data[k] = v
        return new_data

    def _formatting(self, data: t.Mapping):
        if self.convert_object:
            data = self._convert_datetime(data)
        if self.camel:
            data = self._camelcase_key(data)
        return data

    def _convert_request_kwargs(self, kw: dict):
        if 'query_string' in kw and isinstance(kw['query_string'], t.Mapping):
            kw['query_string'] = self._formatting(kw['query_string'])
        if 'json' in kw and isinstance(kw['json'], t.Mapping):
            kw['json'] = self._formatting(kw['json'])

    def open(self, *args, **kwargs):
        response = super().open(*args, **kwargs)
        if self.load_response:
            if response.status_code != 200:
                raise RuntimeError
            response = self.response_cls.load(response.json)
            if response.code != ResponseCode.Success.code:
                print(f'接口调用异常，返回结果:{response.to_dict()}')
            return response
        else:
            return response

    def get(self, *args: t.Any, **kw: t.Any) -> ResponseType:  # type:ignore
        self._convert_request_kwargs(kw=kw)
        return super().get(*args, **kw)  # type:ignore

    def post(self, *args: t.Any, **kw: t.Any) -> ResponseType:  # type:ignore
        self._convert_request_kwargs(kw=kw)
        return super().post(*args, **kw)  # type:ignore

    def put(self, *args: t.Any, **kw: t.Any) -> ResponseType:  # type:ignore
        self._convert_request_kwargs(kw=kw)
        return super().put(*args, **kw)  # type:ignore

    def delete(self, *args: t.Any, **kw: t.Any) -> ResponseType:  # type:ignore
        self._convert_request_kwargs(kw=kw)
        return super().delete(*args, **kw)  # type:ignore


class LesoonDebugTool(DebugToolbarExtension):

    def init_app(self, app: Flask):
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
            if response.mimetype == 'application/json' and request.args.get(
                    '_debug'):
                html_wrapped_response = make_response(
                    render_template_string(
                        wrap_json,
                        response=response.data.decode('utf-8'),
                        http_code=response.status,
                    ),
                    response.status_code,
                )
                return app.process_response(html_wrapped_response)

            return response

        app.after_request(json_to_html)
        super().init_app(app)


class LesoonJsonEncoder(JSONEncoder):

    def default(self, o: t.Any) -> t.Any:
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)
