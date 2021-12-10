from dataclasses import field

import marshmallow as ma

from lesoon_common.dataclass.base import BaseDataClass
from lesoon_common.dataclass.base import dataclass


@dataclass
class TokenUser(BaseDataClass):
    """token中存放的用户信息,通过current_user()获取."""
    # 用户id
    id: int
    # 公司id
    company_id: int
    # 公司编码
    company_code: str = field(metadata={'required': False, 'load_default': ''})
    # 公司名称
    company_name: str = field(metadata={'required': False, 'load_default': ''})
    # 登录名
    login_name: str
    # 用户名称
    user_name: str
    # 用户编号
    user_id: int
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

    @ma.pre_load()
    def pre_process(self, data, **kwargs):
        # TODO: JAVA体系不存在user_id, 加载实例会报错
        if 'userId' not in data:
            data['userId'] = data['id']
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
            'companyName': '-',
            'loginName': '000000',
            'userName': '系统自动生成',
            'userId': -1,
            'ifAdmin': True,
        }
        return cls.load(system_user)
