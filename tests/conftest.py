"""Defines fixtures available to all tests."""
import logging

import pytest
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
    _db = app.db
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture
def test_client(app):
    return app.test_client()
