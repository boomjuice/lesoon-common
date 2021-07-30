from dataclasses import dataclass

import marshmallow as ma
from marshmallow import EXCLUDE

from .utils.str import camelcase


@dataclass(frozen=True)
class TokenUser:
    # 用户id
    id: int
    # 公司id
    company_id: int
    # 邮箱地址
    email: str
    # 手机号
    phone_number: str
    # 组织id
    org_id: int
    # 登录名
    login_name: str
    # 用户图标
    icon: str
    # 用户名称
    user_name: str
    # 用户编号
    user_id: int = 0
    # 员工类型
    employee_attr: str = "2"
    # 逻辑删除
    if_deleted: bool = False
    # 是否管理员
    if_admin: bool = False
    # app版本
    app_version: str = ""
    # app类型
    app_type: str = ""

    @classmethod
    def dump(cls, data, **kwargs):
        return TokenUserSchema().dump(data, **kwargs)

    @classmethod
    def load(cls, data, **kwargs):
        return TokenUserSchema().load(data, **kwargs)

    @classmethod
    def clone(cls, user: object):
        init_kwargs = dict()
        for key in cls.__annotations__.keys():
            init_kwargs[key] = user.__dict__.get(key)
        return TokenUser(**init_kwargs)

    def to_dict(self, **kwargs):
        return TokenUserSchema().dump(self.__dict__, **kwargs)


class TokenUserSchema(ma.Schema):
    id = ma.fields.Int(required=True)
    company_id = ma.fields.Int(required=True)
    email = ma.fields.Str(allow_none=True)
    phone_number = ma.fields.Str(allow_none=True)
    org_id = ma.fields.Int()
    login_name = ma.fields.Str(required=True)
    icon = ma.fields.Str(allow_none=True)
    user_name = ma.fields.Str()
    user_id = ma.fields.Int()
    employee_attr = ma.fields.Str()
    if_deleted = ma.fields.Bool()
    if_admin = ma.fields.Bool()
    app_version = ma.fields.Str(allow_none=True)
    app_type = ma.fields.Str(allow_none=True)

    # 将序列化/反序列化的列名调整成驼峰命名
    def on_bind_field(self, field_name: str, field_obj: ma.fields.Field) -> None:
        field_obj.data_key = camelcase(field_obj.data_key or field_name)

    @ma.post_load()
    def make_user(self, data, **kwargs):
        return TokenUser(**data)

    class Meta:
        unknown: str = EXCLUDE
