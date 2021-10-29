""" 编码基类模块."""
import enum


@enum.unique
class BaseCode(enum.Enum):

    @classmethod
    def is_exist(cls, code: str):
        return code in cls._value2member_map_  # type:ignore[operator]

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # values[0]:code作为唯一键
        obj._value_ = values[0]
        for other_value in values[1:]:
            cls._value2member_map_[other_value] = obj
        obj._all_values = values
        return obj

    def __init__(self, code: str, msg: str, solution: str):
        self.code = code
        self.msg = msg
        self.solution = solution

    def __repr__(self):
        return '<{}.{}: {}>'.format(
            self.__class__.__name__,
            self._name_,
            ', '.join([repr(v) for v in self._all_values]),
        )
