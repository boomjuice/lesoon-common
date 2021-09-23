from flask.blueprints import Blueprint

from .models import User
from .models import UserSchema
from lesoon_common import LesoonApi
from lesoon_common import LesoonResource

bp = Blueprint("test", __name__)
api = LesoonApi(bp)


class UserResource(LesoonResource):
    method_decorators = []
    __model__ = User
    __schema__ = UserSchema
