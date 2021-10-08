from functools import partial

from flask.globals import _lookup_req_object
from flask_jwt_extended import get_current_user
from werkzeug.local import LocalProxy

from lesoon_common.dataclass.base import TokenUser
from lesoon_common.utils.jwt import get_token
from lesoon_common.wrappers import LesoonRequest

current_user: TokenUser = LocalProxy(
    lambda: get_current_user())  # type:ignore[assignment]

request: LesoonRequest = LocalProxy(partial(_lookup_req_object,
                                            "request"))  # type: ignore

token: str = LocalProxy(lambda: get_token())  # type:ignore
