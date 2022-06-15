""" 异常模块."""
import typing as t

from lesoon_common.response import ResponseCode


class ConfigError(Exception):
    """配置异常"""
    pass


class ParseError(Exception):
    """解析异常"""
    pass


class ServiceError(Exception):
    """服务异常"""

    CODE = ResponseCode.Error

    def __init__(self,
                 code: t.Optional[ResponseCode] = None,
                 msg: t.Optional[str] = None,
                 msg_detail: t.Optional[str] = None):
        super().__init__()
        self.code = code or self.__class__.CODE
        self.msg = msg or self.code.msg
        self.msg_detail = msg_detail or self.code.msg

    def __repr__(self):
        return f'{self.code=},{self.msg_detail=}'


class RequestError(ServiceError):
    """请求异常"""

    CODE = ResponseCode.ReqError
