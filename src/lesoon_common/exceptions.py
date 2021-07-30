""" 异常模块."""
import typing as t

from .response import ResponseCode


class ParseError(Exception):
    """请求参数解析异常类"""

    pass


class ResourceAttrError(Exception):
    """资源属性异常"""

    pass


class ServiceError(Exception):
    """服务异常"""

    def __init__(self, code: ResponseCode, msg: t.Optional[str] = None):
        super().__init__()
        self.code = code
        self.msg = msg or code.msg


class RequestError(ServiceError):
    """请求异常"""

    pass
