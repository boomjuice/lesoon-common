from flask.ctx import _request_ctx_stack  # noqa
from flask.ctx import has_app_context
from flask.ctx import has_request_context


def has_jwt_context() -> bool:
    if has_request_context() and getattr(_request_ctx_stack.top, 'jwt', None):
        return True
    else:
        return False
