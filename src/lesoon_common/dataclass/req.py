import typing as t
from dataclasses import dataclass


@dataclass
class PageParam:
    # 是否分页
    if_page: bool = True
    # 页码
    page: int = 1
    # 页面大小
    page_size: int = 25
    # 过滤条件
    where: t.Optional[dict] = None
