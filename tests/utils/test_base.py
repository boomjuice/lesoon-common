import pytest

from lesoon_common.utils.base import AttrDefaultDict
from lesoon_common.utils.base import AttributeDict
from lesoon_common.utils.base import generate_id


class TestStrUtil:

    def test_generate_id_invalid(self):
        with pytest.raises(ValueError):
            generate_id(10)

    def test_generate_id_standard(self):
        r_id = generate_id(20)
        assert type(r_id) == str
        assert len(str(r_id)) == 20

    def test_generate_id_bulk(self):
        r_id_set = set()
        for _ in range(10000):
            r_id_set.add(generate_id(20))
        assert len(r_id_set) / 10000 >= 0.999

    def test_attr_dict_standard(self):
        a = AttributeDict({'id': 1})
        assert a.id == 1
        a.b = 2
        assert a.b == 2

    def test_attr_default_dict(self):
        a = AttrDefaultDict()
        assert a.b is None
        a = AttrDefaultDict(int)
        assert a.b == 0
        a = AttrDefaultDict(list)
        assert isinstance(a.b, list)
