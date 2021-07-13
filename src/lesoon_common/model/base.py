""" 通用Model基类模块. """
from datetime import datetime

from flask_jwt_extended import get_current_user
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.sql.expression import text
from sqlalchemy.types import DateTime
from sqlalchemy.types import String

from ..extensions import db

Model = db.Model


def current_user_attr(key: str):
    def warpper():
        try:
            return get_current_user()[key]
        except RuntimeError:
            return "dev-test"

    return warpper


class IdModel(Model):  # type:ignore
    __abstract__ = True
    id = Column(BIGINT(20), primary_key=True, comment="ID")


class CompanyMixin:
    company_id = Column(
        BIGINT(20),
        nullable=False,
        comment="公司ID",
        default=current_user_attr("companyId"),
    )


class StatusMixin:
    status = Column(
        TINYINT, nullable=False, server_default=text("'1'"), comment="状态 0-禁用 1-启用"
    )


class RemarkMixin:
    remarks = Column(String(255), comment="备注")


class CommonMixin(StatusMixin, RemarkMixin):
    pass


class FixedOpeartorMixin:
    creator = Column(
        String(20), nullable=False, comment="创建人", default=current_user_attr("userName")
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
        index=True,
    )
    modifier = Column(
        String(20), nullable=True, comment="修改人", default=current_user_attr("userName")
    )
    modify_time = Column(DateTime, nullable=True, comment="修改时间", onupdate=datetime.now)
    update_time = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        comment="记录更新时间",
        index=True,
    )


class BaseModel(IdModel, FixedOpeartorMixin):
    __abstract__ = True


class BaseCompanyModel(BaseModel, CompanyMixin):
    __abstract__ = True