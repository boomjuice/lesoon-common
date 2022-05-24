""" 基础web组件模块. """
import logging
import os
import sys
import typing as t

from flask import current_app
from flask import Flask
from flask_restful import Api
from sqlalchemy.exc import DatabaseError
from werkzeug.exceptions import HTTPException

from lesoon_common.code import MysqlCode
from lesoon_common.code import ResponseCode
from lesoon_common.ctx import has_app_context
from lesoon_common.exceptions import ConfigError
from lesoon_common.exceptions import ServiceError
from lesoon_common.extensions import ca
from lesoon_common.extensions import db
from lesoon_common.extensions import hc
from lesoon_common.extensions import jwt
from lesoon_common.extensions import ma
from lesoon_common.extensions import mg
from lesoon_common.extensions import toolbar
from lesoon_common.response import error_response
from lesoon_common.utils.str import camelcase
from lesoon_common.wrappers import LesoonConfig
from lesoon_common.wrappers import LesoonJsonEncoder
from lesoon_common.wrappers import LesoonRequest
from lesoon_common.wrappers import LesoonTestClient
from lesoon_common.wrappers.plugins import Bootstrap

sqlalchemy_codes = {'pymysql': MysqlCode, 'MySQLdb': MysqlCode}


def handle_exception(error: Exception) -> t.Union[HTTPException, dict]:
    """
    全局异常处理.
    处理异常包括: http异常,
                 服务抛出异常,
                 client远程调用异常,
                 sqlalchemy数据库层面异常,
                 未知异常
    Args:
        error: 异常实例

    """
    current_app.logger.exception(error)
    if isinstance(error, HTTPException):
        # http异常
        return error
    elif isinstance(error, ServiceError):
        # 服务异常
        return error_response(code=error.code,
                              msg=error.msg,
                              msg_detail=error.msg_detail)
    elif hasattr(error, 'code') and hasattr(error, 'msg'):
        # 调用异常
        return error_response(code=error.code, msg=error.msg)  # type:ignore
    elif isinstance(error, DatabaseError):
        # 数据库异常
        msg = errmsg = error._message()
        err_pkg = error.orig.__module__.split('.', 1)[0]
        errcode = error.orig.args[0]

        code_class = sqlalchemy_codes.get(err_pkg, None)
        if code_class and code_class.is_exist(errcode):
            msg = code_class(errcode).msg  # type:ignore[call-arg]
        return error_response(code=ResponseCode.DataBaseError,
                              msg=msg,
                              msg_detail=errmsg)
    else:
        # 未知异常
        return error_response(msg_detail=f'{error.__class__} : {str(error)}')


class LesoonFlask(Flask):
    """
    继承flask,实现了默认拓展, 配置加载, 配置引导以及全局异常处理

    Attributes:
        import_name: 见`attr:Flask.import_name`
        config: 应用配置对象, 具体规则见`func:flask.config.from_object`
        bootstrap: 是否开启启动引导,主要是初始化配置以及加载插件等
        extra_extensions: 自定义拓展
        **kwargs: 见`Flask.__init__`
    """
    # 默认拓展
    default_extensions: t.Dict[str, t.Any] = {
        'db': db,
        'ma': ma,
        'mg': mg,
        'ca': ca,
        'jwt': jwt,
        'toolbar': toolbar,
        'hc': hc,
    }

    # request处理类
    request_class = LesoonRequest

    # config配置类
    config_class = LesoonConfig

    # client处理类
    test_client_class = LesoonTestClient

    # 配置文件路径
    config_path = os.environ.get('CONFIG_PATH', 'config.yaml')

    # 缓存配置
    # 因为不在app上下文中无法获取app.config，所以此处需要做类属性的冗余
    cached_config: dict = {}

    # json encoder
    json_encoder = LesoonJsonEncoder

    def __init__(
        self,
        import_name=__package__,
        config: object = None,
        bootstrap: bool = False,
        extra_extensions: t.Optional[t.Dict[str, t.Any]] = None,
        **kwargs,
    ):
        super().__init__(import_name, **kwargs)
        self.registered_extensions = self.default_extensions
        if extra_extensions:
            self.registered_extensions.update(**extra_extensions)

        if bootstrap:
            # 启动引导
            Bootstrap(app=self)
        self.init_config(config=config)
        self.logger.info(repr(self.config))
        self._init_flask()
        self.url_map.strict_slashes = False

    def init_config(self, config: t.Optional[object] = None):
        try:
            config = config or self.config_path
            self.logger.info(f'开始加载应用配置, 配置对象:{config}')
            self.config.from_object(config)
            self.__class__.cached_config = self.config  # type:ignore
        except Exception as e:
            raise ConfigError(f'加载配置异常:{e}')

    def _init_flask(self):
        self._init_logger()
        self._init_extensions()
        self._init_errorhandler()
        self._init_commands()

    def _init_extensions(self):
        for ext_name, ext in self.registered_extensions.items():
            # 注册拓展,注册后可通过self.extensions[key]或app.ext_name获取拓展对象
            ext.init_app(app=self)
            setattr(self, ext_name, ext)

    def _init_errorhandler(self):
        self.register_error_handler(Exception, handle_exception)

    def _init_commands(self):
        pass

    def _init_logger(self):
        # app default logger
        handler = logging.StreamHandler(sys.stdout)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

        # pymongo command logger
        if 'MONGODB_SETTINGS' in self.config:
            try:
                from pymongo.monitoring import register
                from lesoon_common.wrappers import CommandLogger
                register(CommandLogger())
            except Exception as e:
                self.logger.exception(f'Mongo日志器初始化异常：{e}')
