from functools import partial

from flask.globals import _lookup_req_object
from flask_jwt_extended.utils import get_current_user
from werkzeug.local import LocalProxy

from .dataclass import TokenUser
from .wrappers import LesoonRequest

current_user: TokenUser = LocalProxy(
    lambda: get_current_user()
)  # type:ignore[assignment]

request: LesoonRequest = LocalProxy(
    partial(_lookup_req_object, "request")
)  # type: ignore
