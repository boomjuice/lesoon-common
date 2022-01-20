import typing as t

import pytest
from werkzeug.test import TestResponse

from lesoon_common.response import Response


class UnittestBase:

    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, db):
        pass

    @staticmethod
    def load_response(response: t.Union[TestResponse, t.Mapping]) -> Response:
        if isinstance(response, TestResponse):
            response = response.json  # type:ignore
        if not isinstance(response, t.Mapping):
            raise TypeError(f'期望为{t.Mapping},实际为{type(response)}')
        else:
            return Response.load(response)
