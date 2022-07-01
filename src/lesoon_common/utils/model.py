import typing as t

from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.engine.row import Row

from lesoon_common import current_app
from lesoon_common import ServiceError
from lesoon_common.utils.base import AttributeDict

if t.TYPE_CHECKING:
    from lesoon_common.model import BaseModel

_id_cache: t.List[str] = []


def get_distribute_id() -> str:
    """
    获取分布式id.
    注意：id均由分布式id中心提供
    """
    global _id_cache
    if not _id_cache:
        from lesoon_id_center_client.clients import GeneratorClient
        uid_list = GeneratorClient().batch_get_uid(count=current_app.config.get(
            'DISTRIBUTE_ID_CACHE_SIZE', 100)).result
        _id_cache.extend(uid_list)
    return _id_cache.pop()


def get_current_id(context: DefaultExecutionContext) -> int:
    """
    获取当前对象的id值
    注意：因为id取自于Id中心，所以某些列需要跟id相同时可使用改函数
    Args:
        context: Sqlalchemy执行上下文

    Returns:
        当前model对象的id
    """
    return context.get_current_parameters()['id']


def row_to_dict(rows: t.List[Row]) -> t.List[AttributeDict]:
    """
    Sqlalchemy.Engine.Row对象转换为AttributeDict
    备注： 因为Row不支持赋值操作，对于开发不友好
    Args:
        rows: a list of Row

    Returns:
        a list of AttributeDict
    """
    return [AttributeDict(row._mapping) for row in rows]


def dict_to_model(data: dict, model_type: t.Type['BaseModel']):
    """
    Dict对象转换为Model对象
    Args:
        data: 数据字典
        model_type: Model类

    Returns:
        a instance of model_type
    """
    return model_type(
        **{k: v for k, v in data.items() if hasattr(model_type, k)})
