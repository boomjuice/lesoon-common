""" 响应体模块. """
from typing import Any
from typing import NamedTuple


class Code(NamedTuple):
    code: int
    msg: str
    solution: str


class ResponseCode:
    Success = Code(0, "success", "")
    Error = Code(5001, "error", "系统异常")

    RemoteCallErr = Code(3001, "远程调用异常", "请检查应用或传参是否异常")

    ReqParamMiss = Code(4001, "请求参数缺失", "请检查传参是否完整")
    ReqDataMiss = Code(4002, "请求体数据缺失", "请检查请求体传参是否完整")
    ReqFormMiss = Code(4003, "Form表单数据缺失", "请检查Form表单传参是否完整")
    ReqParamError = Code(4004, "请求参数异常", "请检查传参是否正确")
    ReqDataError = Code(4005, "请求体数据异常", "请检查请求体传参是否正确")
    ReqFormError = Code(4006, "Form表单数据异常", "请检查Form表单数据是否正确")

    ValidOpError = Code(4007, "违法操作", "当前操作不合法")

    TokenMiss = Code(4010, "token缺失", "请检查reqest-headers里是否有token")
    TokenExpired = Code(4011, "token过期", "请重新登录或重新获取token")
    TokenInValid = Code(4012, "token违法", "请检查token是否正确")

    LoginError = Code(4021, "登录异常", "请检查用户名或密码是否正常")


class Response:
    def __init__(self, code: Code, **kwargs):
        self.code = code.code
        self.msg = code.msg
        for k, v in kwargs.items():
            if isinstance(v, bytes):
                v = v.decode()
            setattr(self, k, v)

    def to_dict(self) -> dict:
        return self.__dict__


def success_response(result: Any = None, **kwargs) -> dict:
    resp = Response(code=ResponseCode.Success, **kwargs)
    if result:
        if isinstance(result, list):
            resp.rows = result  # type:ignore
        elif isinstance(result, dict):
            resp.data = result  # type:ignore
        else:
            resp.data = result  # type:ignore
    return resp.to_dict()


def error_response(code: Code, **kwargs) -> dict:
    if not code:
        code = ResponseCode.Error
    return Response(code=code, solution=code.solution, **kwargs).to_dict()
