""" 响应体模块. """
import typing
from typing import NamedTuple

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

    def to_dict(self):
        return self.__dict__


def success_response(result: typing.Union[typing.Dict, typing.List] = None, **kwargs):
    resp = Response(code=ResponseCode.success, **kwargs)
    if result:
        if isinstance(result, list):
            resp.rows = result
        elif isinstance(result, dict):
            resp.data = result
        else:
            resp.data = result
    return resp.to_dict()


def error_response(code: Code, **kwargs):
    return Response(code=code, solution=code.solution, **kwargs).to_dict()


def handle_exception(error: Exception):
    if isinstance(error, HTTPException):
        return error
    app.logger.exception(error)
    return error_response(
        code=ResponseCode.error, msg=f"{error.__class__} : {str(error)}"
    )
