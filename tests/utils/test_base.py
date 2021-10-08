import pytest

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
