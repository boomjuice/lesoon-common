""" 默认拓展模块.
在base.LessonFlask中初始化拓展
"""
import sentry_sdk
from flask_caching import Cache
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration

from lesoon_common.wrappers import LesoonDebugTool
from lesoon_common.wrappers import LesoonJwt
from lesoon_common.wrappers import LesoonQuery
from lesoon_common.plugins import HealthCheck

db = SQLAlchemy(query_class=LesoonQuery, session_options={'autoflush': False})
ma = Marshmallow()
ca = Cache()
jwt = LesoonJwt()
toolbar = LesoonDebugTool()
hc = HealthCheck()

sentry_sdk.init(
    dsn=
    "https://86c4b80dff6c45739262a6908a3e17a1@o877412.ingest.sentry.io/5828006",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
)
