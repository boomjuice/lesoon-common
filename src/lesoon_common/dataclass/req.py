import typing as t
from dataclasses import field

import marshmallow as ma

from lesoon_common.dataclass.base import BaseDataClass
from lesoon_common.dataclass.base import dataclass


@dataclass
class PageParam(BaseDataClass):
    # 是否分页
    if_page: bool = True
    # 页码
    page: int = 1
    # 页面大小
    page_size: int = 25
    # 过滤条件 解析时为元组,调用时为字典
    where: t.Any = None
    # 排序条件 解析时为元组,调用时为字典
    sort: t.Any = None


@dataclass
class CascadeDeleteParam(BaseDataClass):
    """
    级联删除参数定义.
    {
        "pkName" : "billNo",
        "pkValues": ["D1010101","D1010102"],
        "detailTables":[{"entityName":"bl_purchase_dtl","refPkName":"billNo"}]
    }
    """

    @dataclass
    class DetailTables(BaseDataClass):
        entity_name: str
        ref_pk_name: str

    # 主表主键
    pk_name: str
    # 主表主键值
    pk_values: t.List[str]
    # 明细表字典
    detail_tables: t.List[DetailTables] = field(metadata={
        'marshmallow_field': ma.fields.Nested(DetailTables.Schema, many=True)
    })
