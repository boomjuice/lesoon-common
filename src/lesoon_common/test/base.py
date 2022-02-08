import typing as t

import pytest
from werkzeug.test import TestResponse

from lesoon_common.response import Response


class UnittestBase:

    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, db):
        pass
