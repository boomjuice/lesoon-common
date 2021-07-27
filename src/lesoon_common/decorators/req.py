import inspect
from functools import wraps
from typing import Any
from typing import Dict
from typing import Optional

from ..exceptions import RequestError
from ..globals import request
from ..response import ResponseCode
from ..utils.str import camelcase


class Param:
    PARAM_MISS_CODE = {
        "args": ResponseCode.ReqParamMiss,
        "json": ResponseCode.ReqDataMiss,
        "form": ResponseCode.ReqFormMiss,
    }

    PARAM_ERROR_CODE = {
        "args": ResponseCode.ReqParamError,
        "json": ResponseCode.ReqDataError,
        "form": ResponseCode.ReqFormError,
    }

    REQUEST_LOCATION = ("args", "json", "form")

    def __init__(
        self,
        key: str,
        default: Any = None,
        loc: str = "args",
        type: Any = str,
        allow_none: bool = False,
        msg: str = "",
    ):
        self.key = key
        self.default = default
        self.type = type

        if loc not in self.REQUEST_LOCATION:
            raise ValueError(f"{loc}是{self.REQUEST_LOCATION}中的值")
        self.loc = loc

        if not msg:
            self.msg = f"传参异常:{key}"

        self.allow_none = allow_none
        self.miss_code = self.PARAM_MISS_CODE[loc]
        self.error_code = self.PARAM_ERROR_CODE[loc]


def _get_request_params(param_dict: Dict[str, Param]) -> dict:
    request_params = dict()
    for arg_name, param in param_dict.items():
        prop = getattr(request, param.loc)
        value = prop.get(param.key, type=param.type, default=param.default)
        if value is None and not param.allow_none:
            raise RequestError(code=param.miss_code, msg=param.msg)
        request_params[arg_name] = value
    return request_params


def request_param(param_dict: Optional[Dict[str, Param]] = None):
    """请求参数解析装饰器.
    示例:
    根据函数签名获取请求参数，如下所示，默认从request.args中获取
        @request_param()
        def get_param(user_id: int, company_id: int):
            pass

    自定义获取类型，如下所示，具体参数见 class.Param
       @request_param({'user_id': Param(key='userId', type=int, loc='args'),
                'company_id': Param(key='companyId', type=int, loc='args')})
        def get_param(user_id: int, company_id: int):
            pass

    """

    def wrapper(fn):
        _param_dict = dict()
        if param_dict:
            _param_dict = param_dict
        else:
            func_params = inspect.signature(fn).parameters
            # 获取函数签名,解析参数
            for arg_name, arg_param in func_params.items():
                kwargs = {"key": camelcase(arg_name)}

                if arg_param.default is not inspect.Parameter.empty:
                    kwargs["default"] = arg_param.default
                if arg_param.annotation is not inspect.Parameter.empty:
                    kwargs["type"] = arg_param.annotation

                _param_dict[arg_name] = Param(**kwargs)

        @wraps(fn)
        def decorator(*args, **kwargs):
            request_param = _get_request_params(_param_dict)
            kwargs.update(request_param)
            return fn(*args, **kwargs)

        return decorator

    return wrapper
