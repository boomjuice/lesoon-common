""" 第三方类库自定义拓展模块. """
import datetime
import typing as t

from flask import Flask
from flask.ctx import has_request_context
from flask.globals import current_app
from flask.globals import request
from flask.helpers import make_response
from flask.templating import render_template_string
from flask.testing import FlaskClient
from flask.wrappers import Request
from flask_debugtoolbar import DebugToolbarExtension
from flask_jwt_extended import JWTManager
from flask_mongoengine import BaseQuerySet
from flask_sqlalchemy import BaseQuery
from jose import jwe
from pymongo.monitoring import CommandListener
from werkzeug.utils import cached_property

from lesoon_common.globals import current_user
from lesoon_common.parse.req import extract_sort_arg
from lesoon_common.parse.req import extract_where_arg
from lesoon_common.parse.sqla import parse_multi_condition
from lesoon_common.parse.sqla import parse_related_models
from lesoon_common.response import error_response
from lesoon_common.response import ResponseCode
from lesoon_common.utils.jwt import get_token
from lesoon_common.utils.str import camelcase


class LesoonRequest(Request):
    PAGE_SIZE_DEFAULT = 25
    PAGE_SIZE_LIMIT = 1000

    @cached_property
    def where(self) -> t.Dict[str, t.Any]:
        where = extract_where_arg(self.args.get('where'))
        return where

    @cached_property
    def sort(self) -> t.List[t.Tuple[str, str]]:
        sort = extract_sort_arg(self.args.get('sort'))
        return sort

    @cached_property
    def if_page(self) -> bool:
        if_page = bool(self.args.get('ifPage', default=1, type=int))
        return if_page

    @cached_property
    def page(self):
        page = self.args.get('page', default=1, type=int)
        if page < 1:
            page = 1
        return page

    @cached_property
    def page_size(self):
        page_size = self.args.get('pageSize',
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


class LesoonJwt(JWTManager):

    def __init__(self, app: t.Optional[Flask] = None):
        super().__init__(app=app)

        # flask_jwt_extended.current_user()的取值函数
        def user_lookup_callback(jwt_headers, jwt_data):
            from lesoon_common.dataclass.user import TokenUser

            return TokenUser.load(jwt_data['userInfo'])

        def invalid_token_callback(msg):
            return error_response(code=ResponseCode.TokenInValid, msg=msg)

        def expired_token_callback(jwt_headers, jwt_data):
            return error_response(code=ResponseCode.TokenExpired)

        self._user_lookup_callback = user_lookup_callback
        self._invalid_token_callback = invalid_token_callback
        self._expired_token_callback = expired_token_callback

    @staticmethod
    def _set_default_configuration_options(app: Flask):
        app.config.setdefault('JWT_ENABLE', False)
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES',
                              datetime.timedelta(days=30))
        app.config.setdefault('JWT_ACCESS_COOKIE_NAME', 'access_token_cookie')
        app.config.setdefault('JWT_ACCESS_COOKIE_PATH', '/')
        app.config.setdefault('JWT_ACCESS_CSRF_COOKIE_NAME',
                              'csrf_access_token')
        app.config.setdefault('JWT_ACCESS_CSRF_COOKIE_PATH', '/')
        app.config.setdefault('JWT_ACCESS_CSRF_FIELD_NAME', 'csrf_token')
        app.config.setdefault('JWT_ACCESS_CSRF_HEADER_NAME', 'X-CSRF-TOKEN')
        app.config.setdefault('JWT_ALGORITHM', 'HS256')
        app.config.setdefault('JWT_COOKIE_CSRF_PROTECT', True)
        app.config.setdefault('JWT_COOKIE_DOMAIN', None)
        app.config.setdefault('JWT_COOKIE_SAMESITE', None)
        app.config.setdefault('JWT_COOKIE_SECURE', False)
        app.config.setdefault('JWT_CSRF_CHECK_FORM', False)
        app.config.setdefault('JWT_CSRF_IN_COOKIES', True)
        app.config.setdefault('JWT_CSRF_METHODS',
                              ['POST', 'PUT', 'PATCH', 'DELETE'])
        app.config.setdefault('JWT_DECODE_ALGORITHMS', None)
        app.config.setdefault('JWT_DECODE_AUDIENCE', None)
        app.config.setdefault('JWT_DECODE_ISSUER', None)
        app.config.setdefault('JWT_DECODE_LEEWAY', 0)
        app.config.setdefault('JWT_ENCODE_AUDIENCE', None)
        app.config.setdefault('JWT_ENCODE_ISSUER', None)
        app.config.setdefault('JWT_ERROR_MESSAGE_KEY', 'msg')
        app.config.setdefault('JWT_HEADER_NAME', 'token')
        app.config.setdefault('JWT_HEADER_TYPE', None)
        app.config.setdefault('JWT_IDENTITY_CLAIM', 'sub')
        app.config.setdefault('JWT_JSON_KEY', 'access_token')
        app.config.setdefault('JWT_PRIVATE_KEY', None)
        app.config.setdefault('JWT_PUBLIC_KEY', None)
        app.config.setdefault('JWT_QUERY_STRING_NAME', 'token')
        app.config.setdefault('JWT_QUERY_STRING_VALUE_PREFIX', '')
        app.config.setdefault('JWT_REFRESH_COOKIE_NAME', 'refresh_token_cookie')
        app.config.setdefault('JWT_REFRESH_COOKIE_PATH', '/')
        app.config.setdefault('JWT_REFRESH_CSRF_COOKIE_NAME',
                              'csrf_refresh_token')
        app.config.setdefault('JWT_REFRESH_CSRF_COOKIE_PATH', '/')
        app.config.setdefault('JWT_REFRESH_CSRF_FIELD_NAME', 'csrf_token')
        app.config.setdefault('JWT_REFRESH_CSRF_HEADER_NAME', 'X-CSRF-TOKEN')
        app.config.setdefault('JWT_REFRESH_JSON_KEY', 'refresh_token')
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES',
                              datetime.timedelta(days=30))
        app.config.setdefault('JWT_SECRET_KEY', None)
        app.config.setdefault('JWT_SESSION_COOKIE', True)
        app.config.setdefault('JWT_TOKEN_LOCATION', ('headers', 'query_string'))
        app.config.setdefault('JWT_ENCODE_NBF', False)

    def _encode_jwt_from_config(
        self,
        identity,
        token_type,
        claims=None,
        fresh=False,
        expires_delta=None,
        headers=None,
    ):
        jwt_token = super()._encode_jwt_from_config(identity, token_type,
                                                    claims, fresh,
                                                    expires_delta, headers)
        secret = current_app.config.get('JWT_SECRET_KEY')
        return jwe.encrypt(jwt_token, key=secret, cty='JWT').decode()


class LesoonTestClient(FlaskClient):

    def __init__(self,
                 *args: t.Any,
                 camel: bool = False,
                 **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.camel = camel

    def _camelcase_key(self, data: t.Mapping):
        return {camelcase(k): v for k, v in data.items()}

    def _convert_request_kwargs(self, kw: dict):
        if self.camel:
            if 'query_string' in kw and isinstance(kw['query_string'],
                                                   t.Mapping):
                kw['query_string'] = self._camelcase_key(kw['query_string'])

            if 'json' in kw and isinstance(kw['json'], t.Mapping):
                kw['json'] = self._camelcase_key(kw['json'])

    def get(self, *args: t.Any, **kw: t.Any):
        self._convert_request_kwargs(kw=kw)
        return super().get(*args, **kw)

    def post(self, *args: t.Any, **kw: t.Any):
        self._convert_request_kwargs(kw=kw)
        return super().post(*args, **kw)

    def put(self, *args: t.Any, **kw: t.Any):
        self._convert_request_kwargs(kw=kw)
        return super().put(*args, **kw)

    def delete(self, *args: t.Any, **kw: t.Any):
        self._convert_request_kwargs(kw=kw)
        return super().delete(*args, **kw)


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


class CommandLogger(CommandListener):

    def started(self, event):
        current_app.logger.debug('Command {0.command_name} with request id '
                                 '{0.request_id} started on server '
                                 '{0.connection_id}'.format(event))

    def succeeded(self, event):
        current_app.logger.debug('Command {0.command_name} with request id '
                                 '{0.request_id} on server {0.connection_id} '
                                 'succeeded in {0.duration_micros} '
                                 'microseconds'.format(event))

    def failed(self, event):
        current_app.logger.debug('Command {0.command_name} with request id '
                                 '{0.request_id} on server {0.connection_id} '
                                 'failed in {0.duration_micros} '
                                 'microseconds'.format(event))
