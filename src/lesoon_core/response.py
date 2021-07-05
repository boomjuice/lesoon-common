""" 响应体模块. """
from typing import Any
from typing import NamedTuple
from typing import Union

from flask import current_app as app
from werkzeug.exceptions import HTTPException


class Code(NamedTuple):
    code: int
    msg: str
    solution: str


class ResponseCode:
    success = Code(0, "success", "")
    error = Code(1111, "error", "系统异常")


class Response:
    def __init__(self, code: Code, **kwargs):
        self.code = code.code
        self.msg = kwargs.pop("msg", None) or code.msg
        for k, v in kwargs.items():
            if not hasattr(self, k):
                setattr(self, k, v)

    def to_dict(self) -> dict:
        return self.__dict__


def success_response(result: Any = None, **kwargs) -> dict:
    resp = Response(code=ResponseCode.success, **kwargs)
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
        code = ResponseCode.error
    return Response(code=code, solution=code.solution, **kwargs).to_dict()


def handle_exception(error: Exception) -> Union[HTTPException, dict]:
    if isinstance(error, HTTPException):
        return error
    app.logger.exception(error)
    return error_response(
        code=ResponseCode.error, msg=f"{error.__class__} : {str(error)}"
    )
