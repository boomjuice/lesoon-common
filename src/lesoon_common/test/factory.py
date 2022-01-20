from datetime import datetime
from functools import partial

import factory

from lesoon_common.extensions import db

current_datetime = partial(datetime.strptime,
                           date_string=datetime.now(),
                           format='%Y-%m-%d %H:%M:%S')


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        abstract = True
        sqlalchemy_session = db.session

    id = factory.Sequence(lambda n: n + 1)
    creator = '单元测试'
    create_time = factory.Faker('date_time')
    update_time = factory.Faker('date_time')


class BaseCompanyFactory(BaseFactory):

    class Meta:
        abstract = True

    company_id = 1
