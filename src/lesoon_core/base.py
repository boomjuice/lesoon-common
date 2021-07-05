import logging
import sys
from collections import OrderedDict
from datetime import timedelta
from typing import Any

from flask import Flask
from flask_restful import Api
from werkzeug.datastructures import ImmutableDict

from .extensions import ca
from .extensions import db
from .extensions import ma
from .resource import LesoonResource
from .resource import LesoonResourceItem
from .response import handle_exception
from .utils.base import camelcase


class LesoonFlask(Flask):
    default_extensions = OrderedDict({"db": db, "ma": ma, "ca": ca})

    #: 重写Flask.default_config以减少未配置config的异常
    default_config = ImmutableDict(
        {
            "ENV": None,
            "DEBUG": None,
            "TESTING": False,
            "PROPAGATE_EXCEPTIONS": None,
            "PRESERVE_CONTEXT_ON_EXCEPTION": None,
            "SECRET_KEY": None,
            "PERMANENT_SESSION_LIFETIME": timedelta(days=31),
            "USE_X_SENDFILE": False,
            "SERVER_NAME": None,
            "APPLICATION_ROOT": "/",
            "SESSION_COOKIE_NAME": "session",
            "SESSION_COOKIE_DOMAIN": None,
            "SESSION_COOKIE_PATH": None,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SECURE": False,
            "SESSION_COOKIE_SAMESITE": None,
            "SESSION_REFRESH_EACH_REQUEST": True,
            "MAX_CONTENT_LENGTH": None,
            "SEND_FILE_MAX_AGE_DEFAULT": None,
            "TRAP_BAD_REQUEST_ERRORS": None,
            "TRAP_HTTP_EXCEPTIONS": False,
            "EXPLAIN_TEMPLATE_LOADING": False,
            "PREFERRED_URL_SCHEME": "http",
            "JSON_AS_ASCII": True,
            "JSON_SORT_KEYS": True,
            "JSONIFY_PRETTYPRINT_REGULAR": False,
            "JSONIFY_MIMETYPE": "application/json",
            "TEMPLATES_AUTO_RELOAD": None,
            "MAX_COOKIE_SIZE": 4093,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "CACHE_TYPE": "flask_caching.backends.simple",
        }
    )

    def __init__(
        self,
        import_name=__package__,
        extensions=None,
        **kwargs,
    ):
        super().__init__(import_name, **kwargs)
        extensions: OrderedDict[str, Any] = (
            extensions or self.__class__.default_extensions
        )
        self._init_flask(extensions)

    def _init_flask(self, extensions):
        self._init_extensions(extensions=extensions)
        self._init_errorhandler()
        self._init_commands()
        self._init_logger()

    def _init_extensions(self, extensions):
        for ext_name, ext in extensions.items():
            # 注册拓展,注册后可通过self.extensions[key]或app.key获取拓展对象
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

    def add_extensions(self, extensions):
        new_extensions = dict(extensions.items() - self.extensions.items())
        if new_extensions:
            self._init_extensions(extensions=extensions)
        else:
            self.logger.warn(f"flask 拓展已存在: {new_extensions}")


class LesoonApi(Api):
    def add_resource_item(self, resource, *urls, **kwargs):
        """注册资源项目."""
        # 生成resourceItem类
        cls_attrs = {"__model__": resource.__model__, "__schema__": resource.__schema__}
        resource_item_cls = type(f"{resource}Item", (LesoonResourceItem,), cls_attrs)
        ri_cls = resource.item_cls = resource_item_cls

        # 生成resourceItem 路由参数
        item_endpoint = kwargs.get("endpoint") or camelcase(resource.__class__.lower())
        kwargs["endpoint"] = item_endpoint + "_item"
        kwargs["methods"] = ri_cls.item_lookup_methods
        url_suffix = f"/<{ri_cls.item_lookup_type}:{ri_cls.item_lookup_field}>"
        item_urls = [url + url_suffix for url in urls]
        self.add_resource(resource.item_cls, *item_urls, **kwargs)

    def register_resource(self, resource, *urls, **kwargs):
        """注册资源.
        如果资源设置item_lookup,默认为True,则会追加注册item资源
        """
        if issubclass(resource, LesoonResource):
            if getattr(resource, "item_lookup", True):
                self.add_resource_item(resource, *urls, **kwargs)
        self.add_resource(resource, *urls, **kwargs)
