import typing as t

from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.engine.row import Row

from lesoon_common.utils.base import AttributeDict


def get_distribute_id() -> int:
    """
    获取分布式id.
    注意：id均由分布式id中心提供
    """
    from lesoon_id_center_client.clients import GeneratorClient
    generator_client = GeneratorClient()
    return generator_client.get_uid().result


def get_current_id(context: DefaultExecutionContext) -> int:
    return context.get_current_parameters()['id']


def row_to_dict(rows: t.List[Row]) -> t.List[AttributeDict]:
    return [AttributeDict(row._asdict()) for row in rows]
