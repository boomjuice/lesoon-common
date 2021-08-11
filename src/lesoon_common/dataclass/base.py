from dataclasses import dataclass

import marshmallow as ma

from ..model import fields
from ..model.schema import CamelSchema


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
        return TokenUser(**init_kwargs)  # type:ignore[arg-type]

    def to_dict(self, **kwargs):
        return TokenUserSchema().dump(self.__dict__, **kwargs)


class TokenUserSchema(CamelSchema):
    id = fields.Int(required=True)
    company_id = fields.Int(required=True)
    email = fields.Str(allow_none=True)
    phone_number = fields.Str(allow_none=True)
    org_id = fields.Int()
    login_name = fields.Str(required=True)
    icon = fields.Str(allow_none=True)
    user_name = fields.Str()
    user_id = fields.Int()
    employee_attr = fields.Str()
    if_deleted = fields.Bool()
    if_admin = fields.Bool()
    app_version = fields.Str(allow_none=True)
    app_type = fields.Str(allow_none=True)

    @ma.post_load
    def make_user(self, data, **kwargs):
        return TokenUser(**data)

    class Meta:
        unknown: str = ma.EXCLUDE
