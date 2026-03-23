from typing import Generic

from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import (
    ScissorsEffectRangeMode,
    SegmentationEffectScissors,
)

from ...ui import ScissorsEffectState, SegmentEditorUI
from .base_segmentation_logic import BaseEffectLogic, U


class ScissorsEffectLogic(BaseEffectLogic[ScissorsEffectState, U], Generic[U]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, ScissorsEffectState, SegmentationEffectScissors)
        self.bind_changes(
            {
                self.name.fill_mode: self._on_fill_mode_changed,
                self.name.range_mode: self._on_range_mode_changed,
                self.name.symmetric_distance: self._on_symmetric_distance_changed,
            }
        )

    @property
    def effect(self) -> SegmentationEffectScissors:
        return super().effect

    def set_ui(self, ui: SegmentEditorUI):
        pass

    def _on_fill_mode_changed(self, fill_mode):
        if not self.is_active():
            return
        self.effect.set_fill_mode(fill_mode)

    def _on_range_mode_changed(self, range_mode: ScissorsEffectRangeMode):
        if not self.is_active():
            return
        self.effect.set_range_mode(range_mode)

    def _on_symmetric_distance_changed(self, symmetric_distance: float):
        if not self.is_active():
            return
        self.effect.set_symmetric_distance(symmetric_distance)
