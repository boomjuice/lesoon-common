""" 返回码模块."""
from lesoon_common.code.base import BaseCode


class ResponseCode(BaseCode):
    Success = ('0', '操作成功', '')
    Error = ('5001', '系统异常', '系统异常')

    RemoteCallError = ('3001', '远程调用异常', '请检查应用或传参是否异常')

    ReqError = ('4000', '请求异常', '请检查请求是否合法')
    ReqParamMiss = ('4001', '请求参数缺失', '请检查传参是否完整')
    ReqBodyMiss = ('4002', '请求体数据缺失', '请检查请求体传参是否完整')
    ReqFormMiss = ('4003', 'Form表单数据缺失', '请检查Form表单传参是否完整')
    ReqParamError = ('4004', '请求参数异常', '请检查传参是否正确')
    ReqBodyError = ('4005', '请求体数据异常', '请检查请求体传参是否正确')
    ReqFormError = ('4006', 'Form表单数据异常', '请检查Form表单数据是否正确')

    ValidOpError = ('4007', '违法操作', '当前操作不合法')

    DataBaseError = ('4500', '数据库异常', '请检查数据库或者数据是否正确')

    TokenMiss = ('4010', 'token缺失', '请检查请求是否携带token')
    TokenExpired = ('4011', 'token过期', '请重新登录或重新获取token')
    TokenInValid = ('4012', 'token违法', '请检查token是否正确')

    LoginError = ('4020', '登录异常', '请检查用户名或密码是否正常')
    NotFoundError = ('4041', '查询异常', '当前查询参数没有对应结果')
