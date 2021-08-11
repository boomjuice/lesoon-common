import inspect
import typing as t
from collections import OrderedDict
from functools import wraps

from flask import Blueprint
from flask import Flask
from flask import request
from flask.wrappers import ResponseBase
from flask_restful import unpack

from .dataclass.resource import ImportData
from .exceptions import RequestError
from .resource import BaseResource
from .resource import LesoonResource
from .response import ResponseCode
from .response import success_response
from .utils.jwt import jwt_required
from .utils.req import Param
from .utils.req import request_param
from .utils.str import udlcase


def route(rule: str, skip_decorator: bool = False, **options: t.Any) -> t.Callable:
    """一个用于标示路由的装饰器,使用在BaseView的子类中，
    与 `@app.route`使用类相同
    """

    def decorator(f: t.Callable) -> t.Callable:
        f._rule_cache = (rule, options)  # type:ignore[attr-defined]
        f.skip_decorator = skip_decorator  # type:ignore[attr-defined]
        return f

    return decorator


def get_route_members(base_cls, cls):
    base_members = dir(base_cls)
    all_members = inspect.getmembers(cls, predicate=inspect.isfunction)
    return [
        member
        for member in all_members
        if member[0] not in base_members and hasattr(member[1], "_rule_cache")
    ]


class BaseView:
    url: str = ""

    resource: t.Type[BaseResource] = None  # type:ignore

    representations: t.Dict[str, t.Callable] = {}

    method_decorators: t.List[t.Callable] = []

    @classmethod
    def register(
        cls,
        app: t.Union[Flask, Blueprint],
        url: t.Optional[str] = None,
        endpoint: t.Optional[str] = None,
        base_cls=None,
        **rule_options
    ):

        url = url or cls.url
        base_cls = base_cls or BaseView

        # 获取需要路由的方法
        members = get_route_members(base_cls, cls)

        bp = Blueprint(
            name=endpoint or udlcase(cls.__name__), import_name=__name__, url_prefix=url
        )

        for name, func in members:
            rule, options = func._rule_cache
            view_func = cls.make_view_func(name, func.skip_decorator)
            func_endpoint = options.pop("endpoint", None)

            bp.add_url_rule(
                rule=rule, endpoint=func_endpoint, view_func=view_func, **options
            )

        app.register_blueprint(bp)

    @classmethod
    def make_view_func(cls, name: str, skip_decorator: bool):
        instance = cls()

        view = getattr(instance, name)

        def make_func(fn):
            @wraps(fn)
            def decorator(*args, **kwargs):
                return fn(*args, **kwargs)

            return decorator

        view = make_func(view)
        view.__module__ = cls.__module__
        view.__doc__ = cls.__doc__
        view._instance = instance

        if not skip_decorator:
            for decorator in cls.method_decorators:
                view = decorator(view)

        @wraps(view)
        def view_func(*args, **kwargs):
            resp = view(*args, **kwargs)

            if isinstance(resp, ResponseBase):
                return resp

            representations = cls.representations or OrderedDict()

            mediatype = request.accept_mimetypes.best_match(
                representations, default=None
            )
            if mediatype in representations:
                data, code, headers = unpack(resp)
                resp = representations[mediatype](data, code, headers)
                resp.headers["Content-Type"] = mediatype
                return resp

            return resp

        return view_func


class LesoonView(BaseView):
    resource: t.Type[LesoonResource] = None  # type:ignore

    method_decorators = [jwt_required()]

    @route("/save", methods=["POST"])
    @request_param(
        {
            "insert_rows": Param(key="insertRows", loc="body", type=list),
            "update_rows": Param(key="updateRows", loc="body", type=list),
            "delete_rows": Param(key="deleteRows", loc="body", type=list),
        }
    )
    def union_operate(self, insert_rows: list, update_rows: list, delete_rows: list):
        """增删改合并操作."""
        self.resource.union_operate(insert_rows, update_rows, delete_rows)
        return success_response()

    @route("/importData", methods=["POST"])
    @request_param({"req_data": Param(loc="body")})
    def import_data(self, req_data: dict):
        """数据导入."""
        import_data: ImportData = ImportData.load(req_data)
        if not import_data.data_list:
            raise RequestError(code=ResponseCode.ReqBodyError, msg="导入数据为空")
        return self.resource.import_data(import_data)
