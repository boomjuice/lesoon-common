from lesoon_common.utils.req import Param
from lesoon_common.utils.req import request_param


class TestReqUtil:

    def test_request_param_with_func_sign(self):

        @request_param()
        def simple(a_b: int, b_c: str = None):
            pass

        assert simple._param_dict['a_b'] == Param(key='aB', data_type=int)
        assert simple._param_dict['b_c'] == Param(key='bC',
                                                  data_type=str,
                                                  default=None)

    def test_request_param_with_camelcase_key(self):

        @request_param(camelcase_key=False)
        def simple(a_b: int, a_c: str = None):
            pass

        assert simple._param_dict['a_b'] == Param(key='a_b', data_type=int)
        assert simple._param_dict['a_c'] == Param(key='a_c',
                                                  data_type=str,
                                                  default=None)

    def test_request_param_with_param_dict(self):

        @request_param(
            param_dict={
                'a': Param(key='a', data_type=int, loc='body'),
                'b': Param(key='b', data_type=str, default=None),
            })
        def simple(a, b):
            pass

        assert simple._param_dict['a'] == Param(key='a',
                                                data_type=int,
                                                loc='body')
        assert simple._param_dict['b'] == Param(key='b',
                                                data_type=str,
                                                default=None)
