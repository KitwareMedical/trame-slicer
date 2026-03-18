from __future__ import annotations

from collections.abc import Callable

from slicer import (
    vtkMRMLInteractionEventData,
)
from vtkmodules.vtkCommonCore import vtkCommand

from .segmentation_effect_islands import SegmentationEffectIslands
from .segmentation_effect_pipeline import SegmentationEffectPipeline


class SegmentationIslandsPipeline(SegmentationEffectPipeline[SegmentationEffectIslands]):
    def __init__(self) -> None:
        super().__init__()

        self._supported_events: dict[int, Callable] = {
            int(vtkCommand.LeftButtonPressEvent): self._LeftButtonPress,
        }

    def IsSupportedEvent(self, event_data: vtkMRMLInteractionEventData):
        return event_data.GetType() in self._supported_events

    def ProcessInteractionEvent(self, event_data: vtkMRMLInteractionEventData) -> bool:
        callback = self._supported_events.get(event_data.GetType())
        return callback(event_data) if callback is not None else False

    def CanProcessInteractionEvent(self, eventData: vtkMRMLInteractionEventData) -> tuple[bool, float]:
        can_process = self.IsActive() and self._effect.is_in_interactive_mode() and self.IsSupportedEvent(eventData)
        return can_process, 0

    def _LeftButtonPress(self, event_data: vtkMRMLInteractionEventData) -> bool:
        self._effect.select_island_at_position(event_data.GetWorldPosition())
        return True
