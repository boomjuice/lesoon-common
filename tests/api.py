from flask.blueprints import Blueprint

from lesoon_common import LesoonApi
from lesoon_common import LesoonResource

from .models import User
from .models import UserSchema

bp = Blueprint("test", __name__)
api = LesoonApi(bp)


class UserResource(LesoonResource):
    __model__ = User
    __schema__ = UserSchema
