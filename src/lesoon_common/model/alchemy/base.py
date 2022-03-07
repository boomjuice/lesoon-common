""" 通用Model基类模块. """
import typing as t
from datetime import datetime

from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.sql.expression import BinaryExpression
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.schema import Column
from sqlalchemy.types import DateTime
from sqlalchemy.types import String

from lesoon_common.extensions import db
from lesoon_common.globals import current_user
from lesoon_common.utils.model import get_distribute_id

Model = db.Model


class IdModel(Model):  # type:ignore
    __abstract__ = True

    id = Column(BIGINT(20),
                primary_key=True,
                autoincrement=True,
                comment='ID',
                default=get_distribute_id)


class CompanyMixin:
    company_id = Column(
        BIGINT(20),
        nullable=False,
        comment='公司ID',
        default=lambda: current_user.company_id,
    )


class StatusMixin:
    status = Column(TINYINT,
                    nullable=False,
                    server_default=text("'1'"),
                    comment='状态 0-禁用 1-启用')


class RemarkMixin:
    remarks = Column(String(255), comment='备注')


class CommonMixin(StatusMixin, RemarkMixin):
    pass


class FixedOperatorMixin:
    creator = Column(
        String(20),
        nullable=False,
        comment='创建人',
        default=lambda: current_user.user_name,
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment='创建时间',
        index=True,
    )
    modifier = Column(
        String(20),
        nullable=True,
        comment='修改人',
        onupdate=lambda: current_user.user_name,
    )
    modify_time = Column(DateTime,
                         nullable=True,
                         comment='修改时间',
                         onupdate=datetime.now)
    update_time = Column(
        DateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'),
        comment='记录更新时间',
        index=True,
    )


class BaseModel(IdModel, FixedOperatorMixin):
    __abstract__ = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BaseCompanyModel(BaseModel, CompanyMixin):
    __abstract__ = True
