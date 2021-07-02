""" 异常模块."""


class ParseError(Exception):
    """请求参数解析异常类"""

    pass


class RequestParamError(Exception):
    """请求参数异常"""

    pass


class ResourceAttrError(Exception):
    """资源属性异常"""

    pass
