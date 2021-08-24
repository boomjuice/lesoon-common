""" 基础web组件模块. """
import logging
import sys
import typing as t

from flask import current_app
from flask import Flask
from flask_restful import Api
from werkzeug.exceptions import HTTPException

from .exceptions import ServiceError
from .extensions import ca
from .extensions import db
from .extensions import jwt
from .extensions import ma
from .extensions import toolbar
from .resource import LesoonResource
from .resource import LesoonResourceItem
from .response import error_response
from .utils.str import camelcase
from .view import LesoonView
from .wrappers import LesoonRequest


def handle_exception(error: Exception) -> t.Union[HTTPException, dict]:
    if isinstance(error, HTTPException):
        return error
    elif isinstance(error, ServiceError):
        return error_response(code=error.code, msg=error.msg)
    else:
        current_app.logger.exception(error)
        return error_response(msg_detail=f"{error.__class__} : {str(error)}")


class LesoonFlask(Flask):
    default_extensions: t.Dict[str, t.Any] = {
        "db": db,
        "ma": ma,
        "ca": ca,
        "jwt": jwt,
        "toolbar": toolbar,
    }

    request_class = LesoonRequest

    def __init__(
        self,
        import_name=__package__,
        config: object = None,
        extra_extensions: t.Optional[t.Dict[str, t.Any]] = None,
        **kwargs,
    ):
        super().__init__(import_name, **kwargs)
        self.config.from_object(config)
        self.registered_extensions = self.default_extensions
        if extra_extensions:
            self.registered_extensions.update(**extra_extensions)
        self._init_flask()

    def _init_flask(self):
        self._init_extensions()
        self._init_errorhandler()
        self._init_commands()
        self._init_logger()

    def _init_extensions(self):
        for ext_name, ext in self.registered_extensions.items():
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


class LesoonApi(Api):
    def add_resource_item(self, resource: t.Type[LesoonResource], *urls, **kwargs):
        """注册资源项目."""
        # 生成resourceItem类
        cls_attrs = {"__model__": resource.__model__, "__schema__": resource.__schema__}
        resource_item_cls: t.Type[LesoonResourceItem] = type(
            f"{resource}Item", (LesoonResourceItem,), cls_attrs
        )
        ri_cls = resource.item_cls = resource_item_cls

        # 生成resourceItem 路由参数
        item_endpoint = kwargs.get("endpoint") or camelcase(resource.__name__)
        kwargs["endpoint"] = item_endpoint + "_item"
        kwargs["methods"] = ri_cls.item_lookup_methods
        url_suffix = f"/<{ri_cls.item_lookup_type}:{ri_cls.item_lookup_field}>"
        item_urls = [url + url_suffix for url in urls]
        self.add_resource(resource.item_cls, *item_urls, **kwargs)

    def register_resource(self, resource: t.Type[LesoonResource], *urls, **kwargs):
        """注册资源.
        如果资源设置item_lookup,默认为True,则会追加注册item资源
        """
        if issubclass(resource, LesoonResource):
            if getattr(resource, "if_item_lookup", True):
                self.add_resource_item(resource, *urls, **kwargs)
        self.add_resource(resource, *urls, **kwargs)

    def register_view(self, view_class: t.Type[LesoonView], url, **kwargs):
        if not issubclass(view_class, LesoonView):
            raise TypeError("reigster_view中的view_class必须为LesoonView的子类")
        view_class.register(self.app, url, **kwargs)
