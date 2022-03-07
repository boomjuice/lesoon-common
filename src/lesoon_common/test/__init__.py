import factory as ft

from .alchemy import BaseCompanyFactory
from .alchemy import BaseFactory
from .alchemy import SqlaFatory
from .base import UnittestBase
from .mock import mock_current_user
from .mock import mock_schema_dict_class
from .mongoengine import MongoFatory

session_mocks = (
    mock_current_user,
    mock_schema_dict_class,
)
