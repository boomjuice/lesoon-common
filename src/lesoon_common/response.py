import typing as t
from collections import Mapping

from lesoon_common.code import ResponseCode


class ResponseBase:
    """
    提供统一的返回体结构.

    Attributes:
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
    def load(cls, data: t.Mapping):
        response = cls(code=ResponseCode.Success)
        response.__dict__.update(**data)
        return response

    def __init__(self, code: ResponseCode, **kwargs):
        self.flag: t.Dict[str, str] = dict()
        self.code = code.code
        self.msg = code.msg
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
        raise NotImplementedError()

    @result.setter
    def result(self, value: t.Any):
        raise NotImplementedError()

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}

    @classmethod
    def success(cls, result: t.Any = None, **kwargs) -> dict:
        resp = cls(code=ResponseCode.Success, result=result, **kwargs)
        return resp.to_dict()

    @classmethod
    def error(cls,
              code: t.Union[ResponseCode, str] = ResponseCode.Error,
              **kwargs) -> dict:
        if isinstance(code, str):
            if ResponseCode.is_exist(code):
                code = ResponseCode(code)  # type:ignore[call-arg]
            else:
                code = ResponseCode.Error
        return cls(code=code, solution=code.solution, **kwargs).to_dict()


class Response(ResponseBase):
    """
    提供统一的外部调用返回体结构.

    Attributes:
        data: 字典类型数据
        rows: 列表类型数据
        code: 返回状态码, 见`lesoon_common.code.ResponseCode`
        **kwargs:
            见 `lesoon_common.response.ResponseBase`
    """

    def __init__(self, code: ResponseCode, **kwargs):
        self.data: t.Dict[str, t.Any] = dict()
        self.rows: t.List[dict] = list()
        super().__init__(code=code, **kwargs)

    @property
    def result(self):
        return self.data or self.rows or None

    @result.setter
    def result(self, value: t.Any):
        if isinstance(value, (list, tuple, set)):
            self.rows = list(value)
        elif isinstance(value, Mapping):
            self.data = dict(value)
        else:
            self.data = value


class ClientResponse(ResponseBase):
    """
    提供统一的内部调用返回体结构.

    Attributes:
       body: 返回数据
       code: 返回状态码, 见`lesoon_common.code.ResponseCode`
       **kwargs:
           见 `lesoon_common.response.ResponseBase`
    """

    def __init__(self, code: ResponseCode, **kwargs):
        self.body: t.Any = None
        super().__init__(code=code, **kwargs)

    @property
    def result(self):
        return self.body or None

    @result.setter
    def result(self, value: t.Any):
        self.body = value


success_response = Response.success
error_response = Response.error
