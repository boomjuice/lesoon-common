import factory

from lesoon_common.extensions import db


class SqlaFatory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        abstract = True
        sqlalchemy_session = db.session


class BaseFactory(SqlaFatory):

    class Meta:
        abstract = True

    id = factory.Sequence(lambda n: n + 1)
    creator = '单元测试'
    create_time = factory.Faker('date_time')
    update_time = factory.Faker('date_time')


class BaseCompanyFactory(BaseFactory):

    class Meta:
        abstract = True

    company_id = 1
