from __future__ import annotations

from .segment_modifier import SegmentModifier


class SegmentationWidget:
    def __init__(self, modifier: SegmentModifier) -> None:
        self._modifier = modifier

    @property
    def modifier(self) -> SegmentModifier:
        return self._modifier
