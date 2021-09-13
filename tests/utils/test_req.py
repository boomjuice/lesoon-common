from lesoon_common.utils.req import Param
from lesoon_common.utils.req import request_param


class TestReqUtil:
    def test_define_param_with_sign(self):
        @request_param()
        def simple(a: int, b: str = None):
            pass

        assert simple._param_dict["a"] == Param(key="a", data_type=int)
        assert simple._param_dict["b"] == Param(key="b", data_type=str, default=None)

    def test_define_param_with_dict(self):
        @request_param(
            param_dict={
                "a": Param(key="a", data_type=int, loc="body"),
                "b": Param(key="b", data_type=str, default=None),
            }
        )
        def simple(a, b):
            pass

        assert simple._param_dict["a"] == Param(key="a", data_type=int, loc="body")
        assert simple._param_dict["b"] == Param(key="b", data_type=str, default=None)
