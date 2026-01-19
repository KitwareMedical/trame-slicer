from typing import Generic

from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import (
    ScissorsSegmentationSliceCut,
    SegmentationEffectScissors,
)

from ...ui import ScissorsEffectState, SegmentEditorUI
from .base_segmentation_logic import BaseEffectLogic, U


class ScissorsEffectLogic(BaseEffectLogic[ScissorsEffectState, U], Generic[U]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, ScissorsEffectState, SegmentationEffectScissors)
        self.bind_changes(
            {
                self.name.operation: self._on_operation_changed,
                self.name.cut_mode: self._on_cut_mode_changed,
                self.name.symmetric_distance: self._on_symmetric_distance_changed,
            }
        )

    def set_ui(self, ui: SegmentEditorUI):
        pass

    def _on_operation_changed(self, _operation):
        if not self.is_active():
            return
        self.effect.set_operation(_operation)

    def _on_cut_mode_changed(self, _cut_mode: ScissorsSegmentationSliceCut):
        if not self.is_active():
            return
        self.effect.set_cut_mode(_cut_mode)

    def _on_symmetric_distance_changed(self, _symmetric_distance: float):
        if not self.is_active():
            return
        self.effect.set_symmetric_distance(_symmetric_distance)
