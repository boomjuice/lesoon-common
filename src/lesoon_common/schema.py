import typing as t

import marshmallow as ma

from lesoon_common.utils.str import camelcase


class BaseSchema(ma.Schema):

    class Meta:
        # 如果load的键没有匹配到定义的field时的操作,
        # RAISE: 如果存在未知key,引发ValidationError
        # EXCLUDE: 忽略未知key
        # INCLUDE: 包含未知可以,即使时未定义的field
        unknown: str = ma.EXCLUDE
        # 排除字段
        exclude: list = []
        # 保持有序
        ordered = True
        # 时间格式
        datetimeformat = '%Y-%m-%d %H:%M:%S'


class CamelSchema(BaseSchema):
    # 将序列化/反序列化的列名调整成驼峰命名
    def on_bind_field(self, field_name: str,
                      field_obj: ma.fields.Field) -> None:
        field_obj.data_key = camelcase(field_obj.data_key or field_name)

    @ma.pre_load
    def camelcase_dict_keys(self, data: t.Any, **kwargs):
        new_data = data
        if isinstance(data, dict):
            new_data = {camelcase(k): v for k, v in data.items()}
        return new_data
