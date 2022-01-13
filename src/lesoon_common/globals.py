import typing as t
from functools import partial

from flask.globals import _app_ctx_stack
from flask.globals import _lookup_req_object
from werkzeug.local import LocalProxy

from lesoon_common.utils.jwt import get_current_user
from lesoon_common.utils.jwt import get_token

if t.TYPE_CHECKING:
    from lesoon_common.wrappers import LesoonRequest
    from lesoon_common.dataclass.user import TokenUser

current_user: 'TokenUser' = LocalProxy(
    lambda: get_current_user())  # type:ignore[assignment]

request: 'LesoonRequest' = LocalProxy(partial(_lookup_req_object,
                                              'request'))  # type:ignore

token: str = LocalProxy(lambda: get_token())  # type:ignore
