""" 通用Model基类模块. """
from sqlalchemy import Column
from sqlalchemy import text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.types import DateTime
from sqlalchemy.types import String
from flask_jwt_extended import get_current_user

from ..extensions import db

Model = db.Model

current_user_name = lambda: get_current_user()['userName']


class IdModel(Model):  # type:ignore
    __abstract__ = True
    id = Column(BIGINT(20), primary_key=True, comment="ID")


class CompanyMixin:
    company_id = Column(BIGINT(20), nullable=False, comment="公司ID")


class FixedTimeMixin:
    creator = Column(String(20),
                     nullable=False,
                     comment="创建人",
                     default=current_user_name)
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    modifier = Column(String(20),
                      nullable=True,
                      comment="修改人",
                      onupdate=current_user_name)
    modify_time = Column(DateTime, nullable=True, comment="修改时间")
    update_time = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        comment="记录更新时间",
    )


class BaseModel(IdModel, FixedTimeMixin):
    __abstract__ = True


class BaseCompanyModel(BaseModel, CompanyMixin):
    __abstract__ = True
