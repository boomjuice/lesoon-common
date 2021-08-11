import inspect
import typing as t
from functools import wraps

from ..exceptions import RequestError
from ..globals import request
from ..response import ResponseCode
from ..utils.str import camelcase


class Param:
    param_miss_code = {
        "param": ResponseCode.ReqParamMiss,
        "body": ResponseCode.ReqBodyMiss,
        "form": ResponseCode.ReqFormMiss,
    }

    param_error_code = {
        "param": ResponseCode.ReqParamError,
        "body": ResponseCode.ReqBodyError,
        "form": ResponseCode.ReqFormError,
    }

    allow_location = {"param": "args", "body": "json", "form": "form"}

    def __init__(
        self,
        key: t.Optional[str] = None,
        default: t.Any = inspect.Parameter.empty,
        loc: str = "param",
        type: t.Any = str,
        deserialize: t.Any = None,
        msg: str = "",
    ):
        self.key = key
        self.default = default
        self.type = type

        self.deserialize = deserialize or type

        if loc not in self.allow_location.keys():
            raise ValueError(f"{loc}不是{self.allow_location.keys()}中的值")
        self.loc = self.allow_location[loc]

        self.msg = msg or f"传参异常:{key}"

        self.miss_code = self.param_miss_code[loc]
        self.error_code = self.param_error_code[loc]


def _get_request_param(param: Param) -> t.Any:
    prop = getattr(request, param.loc)
    if not prop:
        return param.default

    if not param.key:
        return prop

    value = prop.get(param.key)
    if value is None:
        if param.default is inspect.Parameter.empty:
            raise RequestError(code=param.miss_code, msg=param.msg)
        else:
            return param.default
    else:
        try:
            return param.deserialize(value)
        except ValueError:
            raise RequestError(
                code=param.error_code,
                msg=f"{param.key}类型转换异常 {param.deserialize}:{value}",
            )


def _parse_func_signature(func: t.Callable[..., t.Any]) -> t.Dict[str, Param]:
    """解析函数/方法签名.
    示例:
        if  func = def example(self,user_id:int=None)
        return  {'user_id':Param(key='userId', type=int, loc='args')}
    """
    # 获取请求函数签名,解析参数
    param_dict = dict()
    func_params = inspect.signature(func).parameters

    for arg_name, arg_param in func_params.items():
        # 类方法特殊处理
        if arg_name == "self":
            continue

        param = Param(
            key=camelcase(arg_name),
            default=arg_param.default,
            type=arg_param.annotation,
        )
        param_dict[arg_name] = param

    return param_dict


def request_param(
    param_dict: t.Optional[t.Dict[str, Param]] = None,
    extend_param_dict: t.Optional[t.Dict[str, Param]] = None,
):
    """请求参数解析装饰器.
    示例:
    1. 根据函数签名获取请求参数，如下所示，默认从request.args中获取
        @request_param()
        def get_param(user_id: int, company_id: int):
            pass

    2. 修改自动生成部分定义，例如某些需要自定义反序列的类型
       @request_param(extend_param_dict={
        'resource_ids': Param(key='resourceIds', type=list,
                          deserialize=ast.literal_eval, default=list())})
        def get_projects(company_id: int, resource_ids: list):
            pass

    3. 自定义获取类型，如下所示，具体参数见 class.Param
       @request_param({'user_id': Param(key='userId', type=int, loc='args'),
                'company_id': Param(key='companyId', type=int, loc='args')})
       def get_param(user_id: int, company_id: int):
            pass



    """
    if param_dict and extend_param_dict:
        raise RuntimeError("param_dict 和 extend_param_dict 只可以定义一个")

    def wrapper(fn):
        if param_dict:
            _param_dict = param_dict
        else:
            _param_dict = _parse_func_signature(fn)
            if extend_param_dict:
                _param_dict.update(**extend_param_dict)
        fn._param_dict = _param_dict  # type:ignore[attr-defined]

        @wraps(fn)
        def decorator(*args, **kwargs):
            if kwargs:
                # 直接调用情况不做参数注入
                return fn(*args, **kwargs)
            else:
                # 请求调用情况做参数注入
                for arg_name, param in fn._param_dict.items():
                    kwargs[arg_name] = _get_request_param(param)
                return fn(*args, **kwargs)

        return decorator

    return wrapper
