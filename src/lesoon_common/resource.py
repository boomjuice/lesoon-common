"""资源基类模块.
提供对资源的通用的增删改查
"""
import typing as t
from contextlib import contextmanager

from flask.globals import current_app
from flask.views import MethodViewType
from flask_restful import Resource
from flask_sqlalchemy import get_state
from flask_sqlalchemy import Model
from flask_sqlalchemy import Pagination
from sqlalchemy.orm.session import Session

from lesoon_common.code import ResponseCode
from lesoon_common.dataclass.req import CascadeDeleteParam
from lesoon_common.dataclass.resource import ImportData
from lesoon_common.dataclass.resource import ImportParseResult
from lesoon_common.exceptions import ResourceDefindError
from lesoon_common.exceptions import ServiceError
from lesoon_common.globals import request
from lesoon_common.model.base import BaseCompanyModel
from lesoon_common.model.base import BaseModel
from lesoon_common.model.schema import SqlaCamelSchema
from lesoon_common.parse.sqla import parse_valid_model_attribute
from lesoon_common.parse.sqla import SqlaExpList
from lesoon_common.response import error_response
from lesoon_common.response import success_response
from lesoon_common.utils.jwt import jwt_required
from lesoon_common.utils.resource import parse_import_data
from lesoon_common.utils.str import udlcase
from lesoon_common.wrappers import LesoonQuery


@contextmanager
def session_scope():
    session = get_state(current_app).db.session
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise


class BaseResource(Resource):
    """ 通用增删改查基类."""
    # 资源的Model对象
    __model__: t.Type[BaseModel] = None  # type:ignore
    # 资源的Schema对象
    __schema__: t.Type[SqlaCamelSchema] = None  # type:ignore

    # 资源名称
    _name: t.Optional[str] = None
    # schema实例
    _schema: t.Optional[SqlaCamelSchema] = None
    # 删除基准列
    _default_rm_col: str = 'id'

    @classmethod
    def get_schema(cls):
        if not cls._schema:
            cls._schema = cls.__schema__()
        return cls._schema

    @property
    def model(self):
        return self.__model__

    @property
    def schema(self):
        return self.get_schema()

    @property
    def session(self) -> Session:
        session = get_state(current_app).db.session
        if not session.is_active:
            session.begin()
        return session

    def commit(self, flush: bool = False):
        session = self.session
        try:
            if flush:
                session.flush()
            else:
                session.commit()
        except Exception:
            session.rollback()
            raise

    def get_query(self,
                  add_where: bool = True,
                  add_sort: bool = True) -> LesoonQuery:
        """
        获取通用的query对象.
        注意: 此处为通用的更新,删除的query对象出处。
             如需调整分页查询的query对象, 请重写`method:select_filter()`
        Returns:
            query: `type:LesoonQuery`

        """
        query = self.__model__.query  # type:ignore[attr-defined]
        return query.with_request_condition(add_where=add_where,
                                            add_sort=add_sort)

    def select_filter(self) -> LesoonQuery:
        """
        分页查询的query对象.
        """
        return self.get_query()

    def before_page_dump(self, page_result: Pagination):
        """
        分页查询序列化前操作.
        示例： 比方说需要在序列化前将编码转换成名称,调用外部接口等
        """
        pass

    def page_get(
            self,
            query: t.Optional[LesoonQuery] = None,
            schema: t.Optional[SqlaCamelSchema] = None,
            count_query: t.Optional[LesoonQuery] = None) -> t.Tuple[t.Any, int]:
        """
        通用分页查询.

        Args:
            query: sqlalchemy查询对象
            schema: marshmallow序列化模式实例
            count_query: 总计查询query对象
        """
        _query: LesoonQuery = query or self.select_filter()
        _schema: SqlaCamelSchema = schema or self.get_schema()
        page_result = _query.paginate(count_query=count_query)

        self.before_page_dump(page_result=page_result)

        results = _schema.dump(page_result.items, many=True)
        return results, page_result.total

    def before_create_one(self, obj: BaseModel):
        """
        新增前操作.
        Args:
             obj: `self.__model__`对应实例对象

        """
        pass

    def _create_one(self, obj: BaseModel):
        self.session.add(obj)
        return obj

    def after_create_one(self, data: dict, obj: BaseModel):
        """
        新增后操作.
        Args:
             data: `self.__model__`对应的字典
             obj: `self.__model__`实例对象
        """
        pass

    def create_one(self, data: dict):
        """
           新增单条资源入口.
        Args:
            data: `self.__model__`对应的字典

        Returns:
            obj: `self.__model__`实例对象
        """
        obj = self.get_schema().load(data)
        self.before_create_one(obj)
        obj = self._create_one(obj)
        self.after_create_one(data, obj)
        return obj

    def before_create_many(self, objs: t.List[BaseModel]):
        """
        批量新增前操作.
        Args:
            objs: `self.__model__`实例对象列表

        """
        for obj in objs:
            self.before_create_one(obj)

    def _create_many(self, objs: t.List[BaseModel]):
        self.session.add_all(objs)
        return objs

    def after_create_many(self, data_list: t.List[dict],
                          objs: t.List[BaseModel]):
        """
        批量新增后操作.
        Args:
            data_list: `self.__model__`对应的字典列表
            objs: `self.__model__`实例对象列表

        """
        for data, obj in zip(data_list, objs):
            self.after_create_one(data, obj)

    def create_many(self, data_list: t.List[dict]):
        """
           批量新增资源入口.
        Args:
            data_list: `self.__model__`对应的字典列表

        Returns:
            objs: `self.__model__`实例对象列表
        """
        objs = self.get_schema().load(data_list, many=True)
        self.before_create_many(objs)
        objs = self._create_many(objs)
        self.after_create_many(data_list, objs)
        return objs

    def create(self, data: t.Union[dict, t.List[dict]]):
        """新增资源入口."""
        result = None
        if isinstance(data, list):
            self.create_many(data)
        else:
            result = self.create_one(data)
        self.commit()
        result = self.get_schema().dump(result)
        return result

    def update_one(self, data: dict):
        """更新单条资源."""
        obj = self.get_schema().load(data, partial=True)
        _q = self.get_query(add_sort=False).filter(
            self.__model__.id == data.get('id')).first()
        if not _q:
            obj = None
        else:
            obj = self.get_schema().load(data, partial=True, instance=_q)
        return obj

    def update_many(self, data_list: t.List[dict]):
        """批量更新资源."""
        for data in data_list:
            self.update_one(data=data)
        return None

    def update(self, data: t.Union[dict, t.List[dict]]):
        """新增资源入口."""
        result = None
        if isinstance(data, list):
            self.update_many(data)
        else:
            result = self.update_one(data)
        self.commit()
        result = self.get_schema().dump(result)
        return result

    def before_remove_many(self, ids: t.List[str]):
        """批量删除前操作."""
        pass

    def _remove_many(self,
                     ids: t.List[str],
                     filters: t.Optional[SqlaExpList] = None):
        """
        批量刪除.

        Args:
            ids: 刪除的值列表
            filters: sqlalchemy过滤条件. 示例: SysUser.company_id == 1

        """
        attr = parse_valid_model_attribute(self._default_rm_col, self.__model__)
        query: LesoonQuery = self.get_query(add_sort=False).filter(
            attr.in_(ids))
        if filters:
            query = query.filter(*filters)
        query.delete(synchronize_session=False)

    def after_remove_many(self, ids: t.List[str]):
        """批量删除后操作."""
        pass

    def remove_many(self, ids: t.List[str]):
        self.before_remove_many(ids)
        self._remove_many(ids)
        self.after_remove_many(ids)

    def remove(self, ids: t.List[str]):
        """删除资源入口."""
        if not ids:
            return
        self.remove_many(ids)
        self.commit()


class LesoonResourceType(MethodViewType):
    """Resource类定义检测元类."""

    base_classes = {
        'LesoonResource', 'LesoonMultiResource', 'SaasResource',
        'SaasMultiResource'
    }

    register_resources: t.Dict[str, t.Type[BaseResource]] = dict()

    def __new__(mcs, name, bases, d):
        new_cls = super().__new__(mcs, name, bases, d)
        if name not in mcs.base_classes:
            if res_name := getattr(d, '_name', ''):
                # 优先类属性定义
                name = res_name
            elif model := d.get('__model__', None):
                # 其次模型名称
                name = model.__name__ + 'Resource'
            mcs.register_resources[name] = new_cls  # noqa
        return new_cls

    def __init__(cls, name, bases, d):  # noqa
        super().__init__(name, bases, d)
        if name not in cls.base_classes:
            model = d.get('__model__', None)
            schema = d.get('__schema__', None)
            if not model:
                for base in bases:
                    # 父类查找
                    model = model or getattr(base, '__model__')  # noqa:B009
                    schema = schema or getattr(base, '__schema__')  # noqa:B009
            if not model:
                raise ResourceDefindError(f'{name}未定义 __model__属性')

            if not issubclass(model, Model):
                raise ResourceDefindError(f'{name}:{model} 不是期望的类型:{Model}')

            if not schema:
                raise ResourceDefindError(f'{name}未定义 __schema__属性')

            if not issubclass(schema, SqlaCamelSchema):
                raise ResourceDefindError(
                    f'{name}:{schema} 不是期望的类型:{SqlaCamelSchema}')


class LesoonResourceItem(BaseResource):
    item_lookup_type = 'int'
    item_lookup_field = 'id'
    item_lookup_methods = ['GET', 'PUT', 'DELETE']

    @property
    def lookup_field(self):
        return self.item_lookup_field

    def get_one_raw(self, lookup):
        field = getattr(self.model, self.item_lookup_field)
        field_val = lookup[self.lookup_field]
        return self.model.query.filter(field == field_val).first()

    def get(self, **lookup):
        obj = self.get_one_raw(lookup)
        return success_response(result=self.schema.dump(obj))

    def put(self, **lookup):
        return self.update(lookup)

    def delete(self, **lookup):
        if obj := self.get_one_raw(lookup):
            self.session.delete(obj)
            self.session.commit()
        return success_response()


class LesoonResource(BaseResource, metaclass=LesoonResourceType):
    """ 单表资源."""
    if_item_lookup = True

    method_decorators = [jwt_required()]

    def reflect_resource_cls(self, name: str):
        """
        通过名称反射获取对应资源类.
        Args:
            name: 资源名,不包含Resource后缀(SysUser,SysMenu...)

        Returns:
            resource_cls: `type: LesoonResource`
        """
        try:
            resource_cls = LesoonResourceType.register_resources[name +
                                                                 'Resource']
            return resource_cls
        except KeyError:
            msg = f'根据{name}无法查找到对应的资源类'
            current_app.logger.error(msg)
            raise ServiceError(msg=msg)

    def get(self):
        results, total = self.page_get()
        return success_response(result=results, total=total)

    def put(self):
        result = self.update(data=request.json)
        return success_response(result=result, msg='更新成功')

    def post(self):
        result = self.create(data=request.json)
        return success_response(result=result, msg='新建成功'), 201

    def delete(self):
        # ids = 1,2,3..(query-param) or [1,2,3...](request-body)
        ids = request.args.get('ids') or request.get_json(silent=True)
        if isinstance(ids, str):
            ids = ids.strip().split(',')
        if ids and isinstance(ids, list):
            self.remove(ids)
            return success_response(msg='删除成功')
        else:
            return error_response(code=ResponseCode.ReqError, msg='请求参数ids不合法')

    def union_operate(self, insert_rows: list, update_rows: list,
                      delete_rows: list):
        """新增，更新，删除的联合操作."""
        self.create_many(insert_rows)
        self.update_many(update_rows)
        self.remove_many(delete_rows)
        self.commit()

    def before_import_data(self, import_data: ImportData):
        """解析导入数据前置操作."""
        pass

    def before_import_insert_one(self, obj: Model, import_data: ImportData):
        """导入数据写库前操作.
        默认会进行查库校验当前对象是否存在
        """
        union_filter = list()
        for key in import_data.union_key:
            attr = parse_valid_model_attribute(key, self.__model__)
            union_filter.append(attr.__eq__(getattr(obj, udlcase(key))))

        if (len(union_filter) and
                self.__model__.query.filter(*union_filter).count()):
            msg_detail = (f'Excel [{obj.excel_row_pos}行,] '
                          f'根据约束[{import_data.union_key_name}]数据已存在')
            if import_data.validate_all:
                obj.error = msg_detail
            else:
                raise ServiceError(msg=msg_detail)

    def process_import_data(self, import_data: ImportData,
                            import_parse_result: ImportParseResult):
        """导入操作写库逻辑."""
        objs = list()
        for obj in import_parse_result.obj_list:
            self.before_import_insert_one(obj, import_data)
            if hasattr(obj, 'error'):
                import_parse_result.insert_err_list.append(obj.error)
            else:
                objs.append(obj)

        self.session.bulk_save_objects(objs)
        import_parse_result.obj_list = objs
        self.commit()

    def import_data(self, import_data: ImportData):
        """数据导入入口."""
        self.before_import_data(import_data)

        import_parse_result: ImportParseResult = parse_import_data(
            import_data, self.__model__)

        if import_parse_result.parse_err_list:
            msg_detail = '数据异常<br/>' + '<br/>'.join(
                import_parse_result.parse_err_list)
            return error_response(msg='导入异常,请根据错误信息检查数据', msg_detail=msg_detail)

        if not import_parse_result.obj_list:
            msg_detail = '<br/>'.join(import_parse_result.insert_err_list)
            return error_response(msg='未解析到数据', msg_detail=msg_detail)

        self.process_import_data(import_data, import_parse_result)

        self.after_import_data(import_data)

        if import_parse_result.insert_err_list:
            msg_detail = ' \n '.join(import_parse_result.insert_err_list)
            return error_response(
                msg=f'导入结果: '
                f'成功条数[{len(import_parse_result.obj_list)}] '
                f'失败条数[{len(import_parse_result.insert_err_list)}]',
                msg_detail=f'失败信息:{msg_detail}',
            )
        else:
            return success_response(
                msg=f'导入成功: 成功条数[{len(import_parse_result.obj_list)}]')

    def after_import_data(self, import_data: ImportData):
        """导入数据后置操作."""
        pass


class LesoonMultiResource(LesoonResource):
    """ 多表资源."""

    @staticmethod
    def validate_remove(resource: BaseResource,
                        filters: t.Optional[SqlaExpList] = None):
        query = resource.get_query()
        if filters:
            query = query.filter(*filters)
        if delete_rows := query.all():
            # 调用统一的删除入口
            resource.remove_many(
                [getattr(row, resource._default_rm_col) for row in delete_rows])

    def cascade_delete(self, delete_param: CascadeDeleteParam):
        pk_col = parse_valid_model_attribute(name=delete_param.pk_name,
                                             model=self.__model__)
        for detail_table in delete_param.detail_tables:
            # 根据资源名获取资源类
            detail_resource: t.Type[LesoonResource] = self.reflect_resource_cls(
                detail_table.entity_name)
            # 获取关联列对象
            ref_column = parse_valid_model_attribute(detail_table.ref_pk_name,
                                                     detail_resource.__model__)
            # 查询关联表待删除数据
            self.validate_remove(
                resource=detail_resource(),
                filters=[ref_column.in_(delete_param.pk_values)])

        self.validate_remove(resource=self,
                             filters=[pk_col.in_(delete_param.pk_values)])
        self.session.commit()


class SaasResource(LesoonResource):
    """ Saas相关资源.
    Saas相关资源涉及数据库操作都需要带上company_id作过滤条件
    """
    __model__: t.Type[BaseCompanyModel] = None  # type:ignore

    def get_query(self, add_where=True, add_sort=True) -> LesoonQuery:
        query = super().get_query(add_where=add_where, add_sort=add_sort)
        query = query.filter(
            self.__model__.company_id == request.user.company_id)
        return query

    def _create_one(self, obj: BaseCompanyModel):
        obj.company_id = obj.company_id or request.user.company_id
        return super()._create_one(obj=obj)

    def _create_many(self, objs: t.List[BaseCompanyModel]):
        for obj in objs:
            obj.company_id = obj.company_id or request.user.company_id
        return super()._create_many(objs=objs)

    def before_import_data(self, import_data: ImportData):
        # 导入验证唯一键也需要携带company_id过滤
        super().before_import_data(import_data=import_data)
        if (import_data.union_key and
                not import_data.union_key.count('companyId')):
            import_data.union_key.append('companyId')

    def before_import_insert_one(self, obj: BaseCompanyModel,
                                 import_data: ImportData):
        obj.company_id = request.user.company_id
        super().before_import_insert_one(obj, import_data)


class SaasMultiResource(SaasResource, LesoonMultiResource):
    """ Saas多表资源."""
    pass
