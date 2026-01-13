from dataclasses import dataclass
from enum import Enum, auto


class ScissorsSegmentationOperation(Enum):
    ERASE_INSIDE = auto()
    ERASE_OUTSIDE = auto()
    FILL_INSIDE = auto()
    FILL_OUTSIDE = auto()


class ScissorsSegmentationSliceCut(Enum):
    UNLIMITED = auto()
    POSITIVE = auto()
    NEGATIVE = auto()
    SYMMETRIC = auto()


@dataclass
class ScissorsEffectParameters:
    cut_mode: ScissorsSegmentationSliceCut = ScissorsSegmentationSliceCut.UNLIMITED
    operation: ScissorsSegmentationOperation = ScissorsSegmentationOperation.ERASE_INSIDE
    symmetric_distance: float = 0.0
