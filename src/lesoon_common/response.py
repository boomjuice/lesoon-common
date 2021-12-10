""" 响应体模块.
该模块用于统一返回体结构.
Examples:
    {
        "flag": {
                "retCode": "0",
                "retMsg": "操作成功",
                "retDetail": "操作成功"
                },
        "data": {...},
        "rows": [{},...],
        "total": int
    }
"""
import typing as t

from lesoon_common.code import ResponseCode


class Response:
    """
    提供统一的返回体结构.

    Attributes:
        data: 字典类型数据
        rows: 列表类型数据
        code: 返回状态码, 见`lesoon_common.code.ResponseCode`
        msg: 返回信息
        total: 数据总计
        **kwargs:
            在返回结构中设立额外的键值对,示例如下
            r = Response(code=ResponseCode.Sucess,name=test).to_dict()
             {
                "flag": {
                        "retCode": "0",
                        "retMsg": "操作成功",
                        "retDetail": "操作成功"
                        },
                "name": "test"
            }

    """

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
            if v:
                setattr(self, k, v)

    @property
    def code(self):
        return self.flag['retCode']

    @code.setter
    def code(self, value):
        self.flag['retCode'] = value

    @property
    def msg(self):
        return self.flag['retMsg']

    @msg.setter
    def msg(self, value):
        self.flag['retMsg'] = self.flag['retDetail'] = value

    @property
    def solution(self):
        return self.flag.get('solution', '')

    @solution.setter
    def solution(self, value):
        self.flag['solution'] = value

    @property
    def msg_detail(self):
        return self.flag['retDetail']

    @msg_detail.setter
    def msg_detail(self, value):
        self.flag['retDetail'] = value

    @property
    def result(self):
        return self.data or self.rows or None

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


def error_response(code: t.Union[ResponseCode, str] = ResponseCode.Error,
                   **kwargs) -> dict:
    if isinstance(code, str):
        if ResponseCode.is_exist(code):
            code = ResponseCode(code)  # type:ignore[call-arg]
        else:
            code = ResponseCode.Error
    return Response(code=code, solution=code.solution, **kwargs).to_dict()
