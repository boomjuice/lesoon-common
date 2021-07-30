""" 响应体模块. """
import enum
import typing as t


@enum.unique
class ResponseCode(enum.Enum):
    Success = (0, "success", "")
    Error = (5001, "error", "系统异常")

    RemoteCallErr = (3001, "远程调用异常", "请检查应用或传参是否异常")

    ReqParamMiss = (4001, "请求参数缺失", "请检查传参是否完整")
    ReqDataMiss = (4002, "请求体数据缺失", "请检查请求体传参是否完整")
    ReqFormMiss = (4003, "Form表单数据缺失", "请检查Form表单传参是否完整")
    ReqParamError = (4004, "请求参数异常", "请检查传参是否正确")
    ReqDataError = (4005, "请求体数据异常", "请检查请求体传参是否正确")
    ReqFormError = (4006, "Form表单数据异常", "请检查Form表单数据是否正确")

    ValidOpError = (4007, "违法操作", "当前操作不合法")

    TokenMiss = (4010, "token缺失", "请检查reqest-headers里是否有token")
    TokenExpired = (4011, "token过期", "请重新登录或重新获取token")
    TokenInValid = (4012, "token违法", "请检查token是否正确")

    LoginError = (4021, "登录异常", "请检查用户名或密码是否正常")
    NotFoundError = (4041, "查询异常", "当前查询参数没有对应结果")

    def __init__(self, code: int, msg: str, solution: str):
        self.code = code
        self.msg = msg
        self.solution = solution


class Response:
    @classmethod
    def load(cls, data: dict):
        response = cls(code=ResponseCode.Success)
        response.__dict__.update(**data)
        return response

    def __init__(self, code: ResponseCode, **kwargs):
        self.flag: t.Dict[str, str] = dict()
        self.data: t.Dict[str, t.Any] = dict()
        self.rows: t.List[dict] = list()
        self.code = code.code
        self.msg = code.msg
        self.total = 0
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def code(self):
        return self.flag["retCode"]

    @code.setter
    def code(self, value):
        self.flag["retCode"] = str(value)

    @property
    def msg(self):
        return self.flag["retMsg"]

    @msg.setter
    def msg(self, value):
        self.flag["retMsg"] = self.flag["retDetail"] = value

    @property
    def solution(self):
        return self.flag.get("solution", "")

    @solution.setter
    def solution(self, value):
        self.flag["solution"] = value

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}


def success_response(result: t.Any = None, **kwargs) -> dict:
    resp = Response(code=ResponseCode.Success, **kwargs)
    if result:
        if isinstance(result, list):
            resp.rows = result
        elif isinstance(result, dict):
            resp.data = result
        else:
            resp.data = result
    return resp.to_dict()


def error_response(code: ResponseCode, **kwargs) -> dict:
    if not code:
        code = ResponseCode.Error
    return Response(code=code, solution=code.solution, **kwargs).to_dict()
