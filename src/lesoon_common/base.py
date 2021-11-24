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
from lesoon_common.exceptions import ConfigError
from lesoon_common.exceptions import ServiceError
from lesoon_common.extensions import ca
from lesoon_common.extensions import db
from lesoon_common.extensions import hc
from lesoon_common.extensions import jwt
from lesoon_common.extensions import ma
from lesoon_common.extensions import toolbar
from lesoon_common.plugins import Bootstrap
from lesoon_common.resource import LesoonResource
from lesoon_common.resource import LesoonResourceItem
from lesoon_common.response import error_response
from lesoon_common.utils.str import camelcase
from lesoon_common.view import LesoonView
from lesoon_common.wrappers import LesoonRequest

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
        return error_response(code=error.code, msg=error.msg)
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
        'ca': ca,
        'jwt': jwt,
        'toolbar': toolbar,
        'hc': hc,
    }

    request_class = LesoonRequest

    # 配置文件路径
    config_path = os.environ.get('CONFIG_PATH', 'config.Config')

    def __init__(
        self,
        import_name=__package__,
        config: object = None,
        bootstrap: bool = False,
        extra_extensions: t.Optional[t.Dict[str, t.Any]] = None,
        **kwargs,
    ):
        super().__init__(import_name, **kwargs)
        self.init_config(config=config)
        self.registered_extensions = self.default_extensions
        if extra_extensions:
            self.registered_extensions.update(**extra_extensions)

        if bootstrap:
            # 启动引导
            Bootstrap(app=self)
        self._init_flask()

    def init_config(self, config: t.Optional[object] = None):
        try:
            self.config.from_object(config or self.config_path)
        except Exception as e:
            raise ConfigError(f'加载配置异常:{e}')

    def _init_flask(self):
        self._init_extensions()
        self._init_errorhandler()
        self._init_commands()
        self._init_logger()

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
        handler = logging.StreamHandler(sys.stdout)
        if not self.logger.handlers:
            self.logger.addHandler(handler)


class LesoonApi(Api):
    supported_register_classes = {LesoonResource, LesoonView}

    def handle_error(self, error: Exception):
        """
        因为flask-restful并未提供自定义的异常捕获,
        这里直接将异常抛出给flask做全局异常处理.
        Args:
            error: 异常实例
        """
        raise error

    def add_resource_item(self, resource: t.Type[LesoonResource], *urls,
                          **kwargs):
        """注册资源项目."""
        # 生成resourceItem类
        cls_attrs = {
            '__model__': resource.__model__,
            '__schema__': resource.__schema__
        }
        resource_item_cls: t.Type[LesoonResourceItem] = type(
            f'{resource}Item', (LesoonResourceItem,), cls_attrs)
        ri_cls = resource.item_cls = resource_item_cls

        # 生成resourceItem 路由参数
        item_endpoint = kwargs.get('endpoint') or camelcase(resource.__name__)
        kwargs['endpoint'] = item_endpoint + '_item'
        kwargs['methods'] = ri_cls.item_lookup_methods
        url_suffix = f'/<{ri_cls.item_lookup_type}:{ri_cls.item_lookup_field}>'
        item_urls = [url + url_suffix for url in urls]
        self.add_resource(resource.item_cls, *item_urls, **kwargs)

    def register_resource(self, resource: t.Type[LesoonResource], *urls,
                          **kwargs):
        """注册资源.
        如果资源设置item_lookup,默认为True,则会追加注册item资源
        """
        if issubclass(resource, LesoonResource):
            if getattr(resource, 'if_item_lookup', True):
                self.add_resource_item(resource, *urls, **kwargs)
        self.add_resource(resource, *urls, **kwargs)

    def register_view(self, view_class: t.Type[LesoonView], url, **kwargs):
        if not issubclass(view_class, LesoonView):
            raise TypeError('view_class必须为LesoonView的子类')
        view_class.register(self.app, url, **kwargs)

    def register(self, rule_provider: t.Union[t.Type[LesoonResource],
                                              t.Type[LesoonView]], *args,
                 **kwargs):
        if issubclass(rule_provider, LesoonResource):
            self.register_resource(rule_provider, *args, **kwargs)
        elif issubclass(rule_provider, LesoonView):
            self.register_view(rule_provider, *args, **kwargs)
        else:
            raise TypeError(
                f'rule_provider只支持为{self.supported_register_classes}的子类')
