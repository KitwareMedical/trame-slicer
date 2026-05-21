from typing import Generic

from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import (
    BrushInteractionMode,
    ScissorsEffectFillMode,
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
                self.name.brush_interaction_mode: self._on_brush_interaction_mode_changed,
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

    def _on_brush_interaction_mode_changed(self, brush_interaction_mode: BrushInteractionMode):
        if not self.is_active():
            return
        self.effect.set_brush_interaction_mode(brush_interaction_mode)

    def _on_fill_mode_changed(self, fill_mode: ScissorsEffectFillMode):
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

    def _on_effect_changed(self, _effect_name):
        if not self.is_active():
            return
        self.effect.set_brush_interaction_mode(self.data.brush_interaction_mode)
        self.effect.set_fill_mode(self.data.fill_mode)
        self.effect.set_range_mode(self.data.range_mode)
        self.effect.set_symmetric_distance(self.data.symmetric_distance)
