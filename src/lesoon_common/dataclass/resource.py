import typing as t
from dataclasses import dataclass as original_dataclass
from dataclasses import field

import marshmallow as ma
from flask_sqlalchemy import Model

from lesoon_common.dataclass.base import BaseDataClass
from lesoon_common.dataclass.base import dataclass


@dataclass
class ImportData(BaseDataClass):
    """导入数据类."""

    # 列名列表  [a,b,c]
    col_names: t.List[str]
    # 是否必填  [true,false,true]
    must_array: t.List[bool]
    # 联合主键(驼峰) [companyId,userId,loginName]
    union_key: t.List[str] = field(metadata={'allow_none': True})
    # 联合主键名称
    union_key_name: str = field(metadata={'allow_none': True})
    # 是否异步
    if_async: bool = field(metadata={'data_key': 'async'})
    # 异常输出到excel
    err_to_excel: bool
    # 导入数据
    data_list: t.List[t.List[str]] = field(
        metadata={
            'marshmallow_field':
                ma.fields.List(ma.fields.List(ma.fields.Str(allow_none=True)))
        })
    # 是否前置验证 (校验数据库层面重复,写入Excel中)
    validate_all: bool = field(metadata={
        'required': False,
        'load_default': False
    })
    # 主表字段
    master_fields: str = field(metadata={
        'required': False,
        'load_default': None
    })
    # 模块名
    module: str = field(metadata={'required': False, 'load_default': ''})
    # 拓展参数
    params: t.Optional[dict] = field(metadata={
        'required': False,
        'load_default': None
    })
    # 导入接口
    url: str = field(metadata={'required': False, 'load_default': ''})
    # 导入文件名
    file_name: str = field(metadata={'required': False, 'load_default': ''})
    # 导入数据开始下标
    import_start_index: int = field(metadata={
        'required': False,
        'load_default': 2
    })

    @ma.pre_load
    def pre_process(self, data, **kwargs):
        """预处理导入数据,检查数据合法性."""
        data['colNames'] = data['colNames'].strip('').split(',')
        data['mustArray'] = data['mustArray'].strip('').split(',')
        data['unionKey'] = None
        data['unionKeyName'] = data.get('unionKeyName')

        if data.get('unionKey'):
            data['unionKey'] = data.get('unionKey').strip('').split(',')

        if not (data['colNames'] and data['mustArray']):
            raise ma.ValidationError('参数colNames与mustArray不能为空')

        if len(data['colNames']) != len(data['mustArray']):
            raise ma.ValidationError('参数colNames与mustArray长度不一致')
        return data


@original_dataclass
class ImportParseResult:
    """导入数据解析类."""

    # model对象列表
    obj_list: t.List[Model]
    # 解析异常信息列表
    parse_err_list: t.List[str]
    # 写入异常信息列表
    insert_err_list: t.List[str] = field(default_factory=list)
