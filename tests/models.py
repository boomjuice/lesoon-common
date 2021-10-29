from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import String

from lesoon_common.model.base import Model
from lesoon_common.model.schema import fields
from lesoon_common.model.schema import SqlaCamelAutoSchema


class User(Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    login_name = Column(String, unique=True, nullable=False)
    user_name = Column(String)
    status = Column(Boolean, default=True)
    create_time = Column(DateTime, default=func.now())


class UserExt(Model):
    __tablename__ = 'user_ext'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    address = Column(String)
    contact_phone = Column(String)
    create_time = Column(DateTime, default=func.now())


class UserSchema(SqlaCamelAutoSchema):
    id = fields.IntStr()

    def on_bind_field(self, field_name, field_obj) -> None:
        pass

    class Meta(SqlaCamelAutoSchema.Meta):
        model = User
        ordered = False
        exclude = ['create_time', 'status']


class UserExtSchema(SqlaCamelAutoSchema):

    class Meta(SqlaCamelAutoSchema.Meta):
        model = UserExt
        exclude = ['create_time']
