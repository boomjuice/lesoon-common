def get_distribute_id() -> int:
    from lesoon_client import IdCenterClient

    id_center_client = IdCenterClient()
    return id_center_client.get_uid().result
