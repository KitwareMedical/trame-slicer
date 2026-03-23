from enum import Enum, auto


class ScissorsEffectFillMode(Enum):
    ERASE_INSIDE = auto()
    ERASE_OUTSIDE = auto()
    FILL_INSIDE = auto()
    FILL_OUTSIDE = auto()


class ScissorsEffectRangeMode(Enum):
    UNLIMITED = auto()
    POSITIVE = auto()
    NEGATIVE = auto()
    SYMMETRIC = auto()
