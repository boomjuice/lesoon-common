""" 默认拓展模块.
在base.LessonFlask中初始化拓展
"""
import sentry_sdk
from flask_caching import Cache
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration

from .wrappers import LesoonQuery
from .wrappers import LesoonJwt

db = SQLAlchemy(query_class=LesoonQuery)
ma = Marshmallow()
ca = Cache()
jwt = LesoonJwt()
sentry_sdk.init(
    dsn="https://86c4b80dff6c45739262a6908a3e17a1@o877412.ingest.sentry.io/5828006",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
)
