from typing import Generic

from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import BrushInteractionMode, SegmentationEffectDraw

from ...ui import DrawEffectState, SegmentEditorUI
from .base_segmentation_logic import BaseEffectLogic, U


class DrawEffectLogic(BaseEffectLogic[DrawEffectState, U], Generic[U]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, DrawEffectState, SegmentationEffectDraw)
        self.bind_changes(
            {
                self.name.brush_interaction_mode: self._on_brush_interaction_mode_changed,
            }
        )

    @property
    def effect(self) -> SegmentationEffectDraw:
        return super().effect

    def set_ui(self, ui: SegmentEditorUI):
        pass

    def _on_brush_interaction_mode_changed(self, brush_interaction_mode: BrushInteractionMode):
        if not self.is_active():
            return
        self.effect.set_brush_interaction_mode(brush_interaction_mode)
