"""Defines fixtures available to all tests."""
import logging

import pytest
from flask_sqlalchemy import SQLAlchemy
from src.lesoon_core import LesoonFlask


@pytest.fixture
def app():
    """Create application for the tests."""
    app = LesoonFlask(__name__)
    app.testing = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.logger.setLevel(logging.CRITICAL)
    ctx = app.test_request_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture
def db(app):
    """Create database for the tests."""
    return SQLAlchemy(app=app)


@pytest.fixture
def User(db):
    class User(db.Model):
        __tablename__ = "user"
        id = db.Column(db.Integer, primary_key=True)
        login_name = db.Column(db.String, unique=True, nullable=False)
        user_name = db.Column(db.String)
        status = db.Column(db.Boolean, default=True)
        create_time = db.Column(db.DateTime, default=db.func.now())

    db.create_all()
    yield User
    db.drop_all()
