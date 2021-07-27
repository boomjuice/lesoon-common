"""资源基类模块.
提供对资源的通用的增删改查
"""
from typing import Any
from typing import List
from typing import Tuple
from typing import Union

from flask.views import MethodViewType
from flask_restful import Resource
from flask_sqlalchemy import Model
from werkzeug.exceptions import BadRequestKeyError

from .exceptions import ResourceAttrError
from .extensions import db
from .globals import request
from .model.base import BaseModel
from .model.schema import SqlaCamelSchema
from .response import success_response
from .wrappers import LesoonQuery


class BaseResource(Resource):
    __model__ = None
    __schema__ = None

    @classmethod
    def get_schema(cls):
        if not hasattr(cls, "_schema"):
            cls._schema = cls.__schema__()
        return cls._schema

    @property
    def model(self):
        return self.__class__.__model__

    @property
    def schema(self):
        return self.__class__.get_schema()

    @classmethod
    def select_filter(cls) -> LesoonQuery:
        query: LesoonQuery = cls.__model__.query  # type:ignore[attr-defined]
        return query.with_request_condition()

    @classmethod
    def page_get(cls) -> Tuple[Any, int]:
        query: LesoonQuery = cls.select_filter()
        if request.if_page:
            page_query = query.paginate()
            result = page_query.items
            total = page_query.total
        else:
            result = query.all()
            total = query.order_by(None).count()

        results = cls.get_schema().dump(result, many=True)
        return results, total

    @classmethod
    def before_create_one(cls, data: dict):
        """新增前操作."""
        pass

    @classmethod
    def after_create_one(cls, data: dict, _obj: BaseModel):
        """新增后操作."""
        pass

    @classmethod
    def create_one(cls, data: dict):
        """新增单条资源."""
        _obj = cls.get_schema().load(data)
        db.session.add(_obj)
        return _obj

    @classmethod
    def before_create_many(cls, data_list: List[dict]):
        """批量新增前操作."""
        pass

    @classmethod
    def after_create_many(cls, data_list: List[dict], _objs: List[BaseModel]):
        """批量新增后操作."""
        pass

    @classmethod
    def create_many(cls, data_list: List[dict]):
        """批量新增资源."""
        _objs = cls.get_schema().load(data_list, many=True)
        db.session.bulk_save_objects(_objs)
        return _objs

    @classmethod
    def create(cls, data: Union[dict, List[dict]]):
        """新增资源入口."""
        if isinstance(data, list):
            cls.before_create_many(data)
            _objs = cls.create_many(data)
            cls.after_create_many(data, _objs)
            result = None
        else:
            cls.before_create_one(data)
            _obj = cls.create_one(data)
            cls.after_create_one(data, _obj)
            result = _obj

        db.session.commit()
        result = cls.get_schema().dump(result)
        return result

    @classmethod
    def update_one(cls, data: dict):
        """更新单条资源."""
        _obj = cls.get_schema().load(data, partial=True)
        _q = cls.__model__.query.get(data.get("id"))  # type:ignore[attr-defined]
        if not _q:
            _obj = None
        else:
            _obj = cls.get_schema().load(data, partial=True, instance=_q)
        return _obj

    @classmethod
    def update_many(cls, data_list: List[dict]):
        """批量更新资源."""
        for data in data_list:
            cls.update_one(data=data)
        return None

    @classmethod
    def update(cls, data: Union[dict, List[dict]]):
        """新增资源入口."""
        if isinstance(data, list):
            result = cls.update_many(data)
        else:
            result = cls.update_one(data)
        db.session.commit()
        result = cls.get_schema().dump(result)
        return result

    @classmethod
    def delete_in(cls, ids: List[str]):
        if not ids:
            return
        cls.__model__.query.filter(cls.__model__.id.in_(ids)).delete()  # type:ignore


class LesoonResourceType(MethodViewType):
    def __init__(cls, name, bases, d):  # noqa
        super().__init__(name, bases, d)
        if name != "LesoonResource":
            model = None
            schema = None
            if not d.get("__model__", None):
                for base in bases:
                    model = model or getattr(base, "__model__")  # noqa:B009
                    schema = schema or getattr(base, "__schema__")  # noqa:B009
                if not model:
                    raise ResourceAttrError(f"{name}未定义 __model__属性")
                if not issubclass(model, Model):
                    raise ResourceAttrError(f"{name}:{d['__model__']} 不是期望的类型:{Model}")

                if not schema:
                    raise ResourceAttrError(f"{name}未定义 __schema__属性")

                if not issubclass(schema, SqlaCamelSchema):
                    raise ResourceAttrError(
                        f"{name}:{d['__schema__']} 不是期望的类型:{SqlaCamelSchema}"
                    )


class LesoonResourceItem(BaseResource):
    item_lookup_type = "int"
    item_lookup_field = "id"
    item_lookup_methods = ["GET", "PUT", "DELETE"]

    @property
    def lookup_field(self):
        return self.__class__.item_lookup_field

    def get_one_raw(self, lookup):
        field = getattr(self.model, self.item_lookup_field)
        field_val = lookup[self.lookup_field]
        return self.model.query.filter(field == field_val).first()

    def get(self, **lookup):
        _obj = self.get_one_raw(lookup)
        return success_response(result=self.schema.dump(_obj))

    def put(self, **lookup):
        return self.update(lookup)

    def delete(self, **lookup):
        if _obj := self.get_one_raw(lookup):
            db.session.delete(_obj)
            db.session.commit()
        return success_response()


class LesoonResource(BaseResource, metaclass=LesoonResourceType):
    if_item_lookup = True

    def get(self):
        results, total = self.page_get()
        return success_response(result=results, total=total)

    def put(self):
        result = self.__class__.update(data=request.json)
        return success_response(result=result)

    def post(self):
        result = self.__class__.create(data=request.json)
        return success_response(result=result), 201

    def delete(self):
        try:
            ids = request.args.get("ids") or request.json.get("ids")
        except AttributeError:
            raise BadRequestKeyError("缺少请求参数ids")
        ids = ids.strip().split(",")
        if any(ids):
            self.__class__.delete_in(ids)
            db.session.commit()
        return success_response()
