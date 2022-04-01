""" 通用Model基类模块. """
from datetime import datetime

from mongoengine import fields

from lesoon_common.extensions import mg
from lesoon_common.globals import current_user
from lesoon_common.wrappers import LesoonQuerySet

Document = mg.Document


class CompanyMixin:
    company_id = fields.IntField(
        comment='公司ID',
        default=lambda: current_user.company_id,
    )


class FixedOperatorMixin:
    creator = fields.StringField(
        max_length=20,
        required=True,
        comment='创建人',
        default=lambda: current_user.user_name,
    )
    create_time = fields.DateTimeField(
        required=True,
        default=datetime.utcnow,
        comment='创建时间',
    )
    modifier = fields.StringField(
        max_length=20,
        null=True,
        comment='修改人',
    )
    modify_time = fields.DateTimeField(null=True, comment='修改时间')


class BaseDocument(Document, FixedOperatorMixin):  # type:ignore
    meta = {
        'abstract': True,
        'indexes': ['create_time', 'modify_time'],
        'queryset_class': LesoonQuerySet,
        'auto_create_index': True,
    }

    def save(
        self,
        force_insert=False,
        validate=True,
        clean=True,
        write_concern=None,
        cascade=None,
        cascade_kwargs=None,
        _refs=None,
        save_condition=None,
        signal_kwargs=None,
        **kwargs,
    ):
        self.modifier = current_user.user_name
        self.modify_time = datetime.utcnow()
        return super(Document,
                     self).save(force_insert, validate, clean, write_concern,
                                cascade, cascade_kwargs, _refs, save_condition,
                                signal_kwargs, **kwargs)


class BaseCompanyDocument(BaseDocument, CompanyMixin):
    meta = {'abstract': True}
