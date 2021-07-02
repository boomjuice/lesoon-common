"""资源基类模块.
提供对资源的通用的增删改查
"""
from flask import request
from flask.views import MethodViewType
from flask_restful import Resource
from flask_sqlalchemy import Model
from werkzeug.exceptions import BadRequestKeyError

from .exceptions import ResourceAttrError
from .extensions import db
from .model.schema import SqlaCamelSchema
from .parse.request import parse_request
from .parse.sqlalchemy import parse_filter
from .parse.sqlalchemy import parse_sort
from .response import success_response


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


class LesoonResourceType(MethodViewType):
    def __init__(cls, name, bases, d):  # noqa
        super().__init__(name, bases, d)
        if name != "LesoonResource":
            if not d.get("__model__", None):
                raise ResourceAttrError(f"{name}未定义 __model__属性")

            if not issubclass(d["__model__"], Model):
                raise ResourceAttrError(f"{name}:{d['__model__']} 不是期望的类型:{Model}")

            if not d.get("__schema__", None):
                raise ResourceAttrError(f"{name}未定义 __schema__属性")

            if not issubclass(d["__schema__"], SqlaCamelSchema):
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
        _q = self.get_one_raw(lookup)

        return success_response(result=self.schema.dump(_q))

    def put(self, **lookup):
        _q = self.get_one_raw(lookup)
        if not _q:
            result = None
        else:
            _obj = self.schema.load(request.json, partial=True, instance=_q)
            db.session.commit()
            result = self.schema.dump(_obj)
        return success_response(result=result)

    def delete(self, **lookup):
        if _q := self.get_one_raw(lookup):
            db.session.delete(_q)
            db.session.commit()
        return success_response()


class LesoonResource(BaseResource, metaclass=LesoonResourceType):
    if_item_lookup = True

    def get(self):
        req = parse_request()
        filter_exp = parse_filter(req.where, self.model)
        sort_exp = parse_sort(req.sort, self.model)

        query = self.model.query.filter(*filter_exp).order_by(*sort_exp)

        page_query = query.paginate(page=req.page, per_page=req.page_size)
        results = self.schema.dump(page_query.items, many=True)

        return success_response(result=results, total=page_query.total)

    def post(self):
        _obj = self.schema.load(request.json)
        db.session.add(_obj)
        db.session.commit()

        result = self.schema.dump(_obj)
        return success_response(result=result), 201

    def put(self):
        _id = request.json.pop("id") or request.args.get("id") or None
        _q = self.model.query.get(_id)
        if not _q:
            result = None
        else:
            _obj = self.schema.load(request.json, partial=True, instance=_q)
            db.session.commit()
            result = self.schema.dump(_obj)
        return success_response(result=result)

    def delete(self):
        try:
            ids = request.args.get("ids") or request.json.get("ids")
        except AttributeError:
            raise BadRequestKeyError("缺少请求参数ids")
        ids = ids.strip().split(",")
        if any(ids):
            self.model.query.filter(self.model.id.in_(ids)).delete()
            db.session.commit()
        return success_response()
