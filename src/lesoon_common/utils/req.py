import json
import typing as t
from urllib import parse

from lesoon_common.exceptions import ParseError


def convert_dict(param: t.Optional[str] = None,
                 silent: bool = False) -> t.Union[str, t.Dict[str, t.Any]]:
    if param:
        try:
            # 特殊字符转义处理
            param = parse.unquote_plus(param)
            _param = json.loads(param)
            if not isinstance(_param, dict):
                return {}
            else:
                return _param
        except (json.JSONDecodeError, TypeError, Exception):
            if silent:
                return param
            raise ParseError(f'参数无法序列化 {param}')
    else:
        return dict()
