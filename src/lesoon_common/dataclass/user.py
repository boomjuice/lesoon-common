from dataclasses import field

import marshmallow as ma

from lesoon_common.dataclass.base import BaseDataClass
from lesoon_common.dataclass.base import dataclass
from lesoon_common.utils.str import camelcase


@dataclass
class TokenUser(BaseDataClass):
    """token中存放的用户信息,通过current_user()获取."""
    # 用户id
    id: int = field(metadata={
        'required': False,
        'allow_none': True,
        'load_default': -1
    })
    # 公司id
    company_id: int = field(metadata={
        'required': False,
        'allow_none': True,
        'load_default': None
    })
    # 公司编码
    company_code: str = field(metadata={
        'required': False,
        'allow_none': True,
        'load_default': None
    })
    # 公司名称
    company_name: str = field(metadata={
        'required': False,
        'allow_none': True,
        'load_default': None
    })
    # 系统id
    system_id: int = field(metadata={
        'required': False,
        'allow_none': True,
        'load_default': None
    })
    # 登录名
    login_name: str
    # 用户名称
    user_name: str
    # 用户编号
    user_id: int = field(metadata={
        'required': False,
        'allow_none': True,
        'load_default': -1
    })
    # 组织ID
    org_id: int = field(metadata={
        'required': False,
        'allow_none': True,
        'load_default': None
    })
    # 邮箱地址
    email: str = field(metadata={
        'allow_none': True,
        'required': False,
        'load_default': ''
    })
    # 手机号
    phone_number: str = field(metadata={
        'allow_none': True,
        'required': False,
        'load_default': ''
    })
    # 用户图标
    icon: str = field(metadata={
        'allow_none': True,
        'required': False,
        'load_default': ''
    })
    # 员工类型
    employee_attr: str = field(metadata={
        'required': False,
        'load_default': '2'
    })
    # 逻辑删除
    if_deleted: bool = field(metadata={
        'required': False,
        'load_default': False
    })
    # 是否管理员
    if_admin: bool = field(metadata={'required': False, 'load_default': False})
    # token有效时间
    token_expire: int = field(metadata={'required': False, 'load_default': 0})
    # 软件版本号
    version_no: str = field(metadata={
        'required': False,
        'load_default': '',
        'allow_none': True
    })
    # app版本
    app_version: str = field(metadata={
        'required': False,
        'load_default': '',
        'allow_none': True
    })
    # app类型
    app_type: str = field(metadata={
        'required': False,
        'load_default': '',
        'allow_none': True
    })

    @ma.post_dump()
    def dump_process(self, data, **kwargs):
        # TODO: JAVA体系中id为user_id
        data['id'] = data['userId']
        return data

    @classmethod
    def clone(cls, user: object):
        init_kwargs = dict()
        for key in cls.__annotations__.keys():
            init_kwargs[key] = user.__dict__.get(key)
        return TokenUser(**init_kwargs)  # type:ignore

    @classmethod
    def system_default(cls):
        system_user = {
            'id': -1,
            'companyId': 1,
            'loginName': '-',
            'userName': '系统自动生成',
            'userId': -1,
            'systemId': 1,
            'ifAdmin': True
        }
        return cls.load(system_user)

    @classmethod
    def new(cls, **kwargs):
        anonymous_user = {
            'id': -1,
            'loginName': '-',
            'userName': '系统自动生成',
            'userId': -1,
            'ifAdmin': True
        }
        for k, v in kwargs.items():
            anonymous_user[camelcase(k)] = v
        return cls.load(anonymous_user)
