from sqlalchemy.engine.default import DefaultExecutionContext


def get_distribute_id() -> int:
    """
    获取分布式id.
    注意：id均由分布式id中心提供
    """
    from lesoon_client import IdCenterClient

    id_center_client = IdCenterClient()
    return id_center_client.get_uid().result


def get_current_id(context: DefaultExecutionContext) -> int:
    return context.get_current_parameters()['id']
