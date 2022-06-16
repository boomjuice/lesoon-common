import datetime
import typing as t

from flask import Flask
from flask.globals import current_app
from flask_jwt_extended import JWTManager
from jose import jwe

from lesoon_common.code.response import ResponseCode
from lesoon_common.response import error_response


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
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', 30 * 24 * 60 * 60)
        app.config.setdefault('JWT_ACCESS_COOKIE_NAME', 'token')
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
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES',30 * 24 * 60 * 60)
        app.config.setdefault('JWT_SECRET_KEY', None)
        app.config.setdefault('JWT_SESSION_COOKIE', True)
        app.config.setdefault('JWT_TOKEN_LOCATION',
                              ('headers', 'query_string', 'cookies'))
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
