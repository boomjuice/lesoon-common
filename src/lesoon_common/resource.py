"""资源基类模块.
提供对资源的通用的增删改查
"""
import typing as t

from flask.views import MethodViewType
from flask_restful import Resource
from flask_sqlalchemy import Model
from werkzeug.exceptions import BadRequestKeyError

from .dataclass.resource import ImportData
from .dataclass.resource import ImportParseResult
from .exceptions import ResourceAttrError
from .extensions import db
from .globals import request
from .model.base import BaseCompanyModel
from .model.base import BaseModel
from .model.schema import SqlaCamelSchema
from .parse.sqla import parse_attribute_name
from .response import error_response
from .response import success_response
from .utils.jwt import jwt_required
from .utils.resource import parse_import_data
from .utils.str import udlcase
from .wrappers import LesoonQuery


class BaseResource(Resource):
    __model__: t.Type[BaseModel] = None  # type:ignore
    __schema__: t.Type[SqlaCamelSchema] = None  # type:ignore

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
        """通用查询query."""
        query = cls.__model__.query  # type:ignore[attr-defined]
        return query.with_request_condition()

    @classmethod
    def page_get(cls) -> t.Tuple[t.Any, int]:
        """通用分页查询."""
        query: LesoonQuery = cls.select_filter()
        page_query = query.paginate()

        results = cls.get_schema().dump(page_query.items, many=True)
        return results, page_query.total

    @classmethod
    def before_create_one(cls, data: dict):
        """新增前操作."""
        pass

    @classmethod
    def _create_one(cls, data: dict):
        """新增单条资源."""
        _obj = cls.get_schema().load(data)
        db.session.add(_obj)
        return _obj

    @classmethod
    def after_create_one(cls, data: dict, _obj: BaseModel):
        """新增后操作."""
        pass

    @classmethod
    def before_create_many(cls, data_list: t.List[dict]):
        """批量新增前操作."""
        pass

    @classmethod
    def _create_many(cls, data_list: t.List[dict]):
        """批量新增资源."""
        _objs = cls.get_schema().load(data_list, many=True)
        db.session.bulk_save_objects(_objs)
        return _objs

    @classmethod
    def after_create_many(cls, data_list: t.List[dict], _objs: t.List[BaseModel]):
        """批量新增后操作."""
        pass

    @classmethod
    def create_one(cls, data: dict):
        cls.before_create_one(data)
        _obj = cls._create_one(data)
        cls.after_create_one(data, _obj)
        return _obj

    @classmethod
    def create_many(cls, data_list: t.List[dict]):
        cls.before_create_many(data_list)
        _objs = cls._create_many(data_list)
        cls.after_create_many(data_list, _objs)
        return _objs

    @classmethod
    def create(cls, data: t.Union[dict, t.List[dict]]):
        """新增资源入口."""
        result = None
        if isinstance(data, list):
            cls.create_many(data)
        else:
            result = cls.create_one(data)

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
    def update_many(cls, data_list: t.List[dict]):
        """批量更新资源."""
        for data in data_list:
            cls.update_one(data=data)
        return None

    @classmethod
    def update(cls, data: t.Union[dict, t.List[dict]]):
        """新增资源入口."""
        result = None
        if isinstance(data, list):
            cls.update_many(data)
        else:
            result = cls.update_one(data)
        db.session.commit()
        result = cls.get_schema().dump(result)
        return result

    @classmethod
    def before_remove_many(cls, ids: t.List[str]):
        """批量删除前操作."""
        pass

    @classmethod
    def _remove_many(cls, ids: t.List[str]):
        """批量删除."""
        cls.__model__.query.filter(cls.__model__.id.in_(ids)).delete(
            synchronize_session=False
        )

    @classmethod
    def after_remove_many(cls, ids: t.List[str]):
        """批量删除后操作."""
        pass

    @classmethod
    def remove_many(cls, ids: t.List[str]):
        cls.before_remove_many(ids)
        cls._remove_many(ids)
        cls.after_remove_many(ids)

    @classmethod
    def remove(cls, ids: t.List[str]):
        """删除资源入口."""
        if not ids:
            return
        cls.remove_many(ids)
        db.session.commit()


class LesoonResourceType(MethodViewType):
    """Resource类定义检测元类."""

    base_classes = {"LesoonResource", "SaasResource"}

    def __init__(cls, name, bases, d):  # noqa
        super().__init__(name, bases, d)
        if name not in cls.base_classes:
            model = d.get("__model__", None)
            schema = d.get("__schema__", None)
            if not model:
                for base in bases:
                    # 父类查找
                    model = model or getattr(base, "__model__")  # noqa:B009
                    schema = schema or getattr(base, "__schema__")  # noqa:B009
            if not model:
                raise ResourceAttrError(f"{name}未定义 __model__属性")

            if not issubclass(model, Model):
                raise ResourceAttrError(f"{name}:{model} 不是期望的类型:{Model}")

            if not schema:
                raise ResourceAttrError(f"{name}未定义 __schema__属性")

            if not issubclass(schema, SqlaCamelSchema):
                raise ResourceAttrError(f"{name}:{schema} 不是期望的类型:{SqlaCamelSchema}")


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

    method_decorators = [jwt_required()]

    def get(self):
        results, total = self.page_get()
        return success_response(result=results, total=total)

    def put(self):
        result = self.__class__.update(data=request.json)
        return success_response(result=result, msg="更新成功")

    def post(self):
        result = self.__class__.create(data=request.json)
        return success_response(result=result, msg="新建成功"), 201

    def delete(self):
        try:
            ids = request.args.get("ids") or request.json.get("ids")
            ids = ids.strip().split(",")
        except AttributeError:
            raise BadRequestKeyError("缺少请求参数ids")
        if any(ids):
            self.__class__.remove(ids)
        return success_response(msg="删除成功")

    @classmethod
    def union_operate(cls, insert_rows: list, update_rows: list, delete_rows: list):
        """新增，更新，删除的联合操作."""
        cls.create_many(insert_rows)
        cls.update_many(update_rows)
        cls.remove_many(delete_rows)
        db.session.commit()

    @classmethod
    def before_import_data(cls, import_data: ImportData):
        """解析导入数据前置操作."""
        pass

    @classmethod
    def before_import_insert_one(cls, obj: Model, import_data: ImportData):
        """导入数据写库前操作.
        默认会进行查库校验当前对象是否存在
        """
        union_filter = list()
        for key in import_data.union_key:
            attr = parse_attribute_name(key, cls.__model__)
            union_filter.append(attr.__eq__(getattr(obj, udlcase(key))))

        if len(union_filter) and cls.__model__.query.filter(*union_filter).count():
            msg_detail = (
                f"Excel [{obj.excel_row_pos}行,] "
                f"根据约束[{import_data.union_key_name}]数据已存在"
            )
            if import_data.validate_all:
                obj.error = msg_detail
            else:
                raise ValueError(msg_detail)

    @classmethod
    def import_data_process(
        cls, import_data: ImportData, import_parse_result: ImportParseResult
    ):
        """导入操作写库逻辑."""
        _objs = list()
        for obj in import_parse_result.obj_list:
            cls.before_import_insert_one(obj, import_data)
            if hasattr(obj, "error"):
                import_parse_result.insert_err_list.append(obj.error)
            else:
                _objs.append(obj)

        db.session.bulk_save_objects(_objs)
        import_parse_result.obj_list = _objs
        db.session.commit()

    @classmethod
    def import_data(cls, import_data: ImportData):
        """数据导入入口."""
        cls.before_import_data(import_data)

        import_parse_result: ImportParseResult = parse_import_data(
            import_data, cls.__model__
        )

        if import_parse_result.parse_err_list:
            msg_detail = "数据异常<br/>" + "<br/>".join(import_parse_result.parse_err_list)
            return error_response(msg="导入异常,请根据错误信息检查数据", msg_detail=msg_detail)

        if not import_parse_result.obj_list:
            msg_detail = "<br/>".join(import_parse_result.insert_err_list)
            return error_response(msg="未解析到数据", msg_detail=msg_detail)

        cls.import_data_process(import_data, import_parse_result)

        cls.after_import_data(import_data)

        if import_parse_result.insert_err_list:
            return error_response(
                msg=f"导入结果: "
                f"成功条数[{len(import_parse_result.obj_list)}] "
                f"失败条数[{len(import_parse_result.insert_err_list)}]",
                msg_detail=f"失败信息:{import_parse_result.insert_err_list}",
            )
        else:
            return success_response(
                msg=f"导入成功: 成功条数[{len(import_parse_result.obj_list)}]"
            )

    @classmethod
    def after_import_data(cls, import_data: ImportData):
        """导入数据后置操作."""
        pass


class SaasResource(LesoonResource):
    __model__: t.Type[BaseCompanyModel] = None  # type:ignore

    @classmethod
    def select_filter(cls) -> LesoonQuery:
        query = super().select_filter()
        return query.filter(cls.__model__.company_id == request.user.company_id)

    @classmethod
    def _create_one(cls, data: dict):
        # saas相关company_id都需要
        data["companyId"] = data.get("companyId") or request.user.company_id
        return super()._create_one(data=data)

    @classmethod
    def _create_many(cls, data_list: t.List[dict]):
        for data in data_list:
            data["companyId"] = data.get("companyId") or request.user.company_id
        return super()._create_many(data_list=data_list)

    @classmethod
    def before_import_insert_one(cls, obj: BaseCompanyModel, import_data: ImportData):
        # 过滤条件以及唯一约束都要加上companyId做验证
        import_data.union_key.append("companyId")
        obj.company_id = request.user.company_id
        super().before_import_insert_one(obj, import_data)

    @classmethod
    def _remove_many(cls, ids: t.List[str]):
        cls.__model__.query.filter(
            cls.__model__.id.in_(ids),
            cls.__model__.company_id == request.user.company_id,
        ).delete()  # type:ignore
