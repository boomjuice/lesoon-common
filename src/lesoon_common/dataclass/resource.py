import typing as t
from dataclasses import dataclass

import marshmallow as ma
from flask_sqlalchemy import Model

from ..model import fields
from ..model.schema import CamelSchema


@dataclass
class ImportData:
    """导入数据类."""

    # 列名列表  [a,b,c]
    col_names: t.List[str]
    # 是否必填  [true,false,true]
    must_array: t.List[bool]
    # 联合主键
    union_key: t.List[str]
    # 联合主键名称
    union_key_name: str
    # 是否异步
    if_async: bool
    # 异常输出到excel
    err_to_excel: bool
    # 导入数据
    data_list: t.List[list]
    # 是否前置验证
    validate_all: bool = False
    # 主表字段
    master_fields: str = ""
    # 模块名
    module: str = ""
    # 拓展参数
    params: t.Optional[dict] = None
    # 导入接口
    url: str = ""
    # 导入文件名
    file_name: str = ""
    # 导入数据开始下标
    import_start_index: int = 2

    @classmethod
    def load(cls, data, **kwargs):
        return ImportDataSchema().load(data, **kwargs)


class ImportDataSchema(CamelSchema):
    col_names = fields.List(fields.Str())
    must_array = fields.List(fields.Bool())
    union_key = fields.List(fields.Str(), allow_none=True)
    union_key_name = fields.Str(allow_none=True)
    validate_all = fields.Bool()
    master_fields = fields.Dict(allow_none=True)
    if_async = fields.Bool(data_key="async")
    err_to_excel = fields.Bool()
    params = fields.Dict(allow_none=True)
    url = fields.Str()
    module = fields.Str()
    file_name = fields.Str()
    import_start_index = fields.Int()
    data_list = fields.List(fields.List(fields.Str(allow_none=True)))

    @ma.pre_load
    def pre_process(self, data, **kwargs):
        """预处理导入数据,检查数据合法性."""
        data["colNames"] = data["colNames"].strip("").split(",")
        data["mustArray"] = data["mustArray"].strip("").split(",")
        data["unionKey"] = None
        data["unionKeyName"] = data.get("unionKeyName")

        if data.get("unionKey"):
            data["unionKey"] = data.get("unionKey").strip("").split(",")

        if not (data["colNames"] and data["mustArray"]):
            raise ma.ValidationError("参数colNames与mustArray不能为空")

        if len(data["colNames"]) != len(data["mustArray"]):
            raise ma.ValidationError("参数colNames与mustArray长度不一致")
        return data

    @ma.post_load
    def make_data(self, data, **kwargs):
        return ImportData(**data)


@dataclass
class ImportParseResult:
    """导入数据解析类."""

    obj_list: t.List[Model]
    err_output_list: t.List[str]
    err_extract_list: t.List[str]
