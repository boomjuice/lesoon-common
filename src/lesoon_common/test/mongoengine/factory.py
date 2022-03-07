import factory


class MongoFatory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        abstract = True
