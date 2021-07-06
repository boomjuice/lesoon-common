from flask.blueprints import Blueprint
from src.lesoon_core import LesoonApi
from src.lesoon_core import LesoonResource
from tests.models import User
from tests.models import UserSchema

bp = Blueprint("test", __name__)
api = LesoonApi(bp)


class UserResource(LesoonResource):
    __model__ = User
    __schema__ = UserSchema
