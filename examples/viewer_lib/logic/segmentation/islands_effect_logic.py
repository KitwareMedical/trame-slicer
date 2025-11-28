from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import SegmentationEffectIslands

from ...ui import (
    IslandsEffectUI,
    IslandsSegmentationMode,
    IslandsState,
    SegmentEditorUI,
)
from .base_segmentation_logic import BaseEffectLogic


class IslandsEffectLogic(BaseEffectLogic[IslandsState, SegmentationEffectIslands]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, IslandsState, SegmentationEffectIslands)

    def set_ui(self, ui: SegmentEditorUI):
        self.set_effect_ui(ui.get_effect_ui(SegmentationEffectIslands))

    def set_effect_ui(self, islands_ui: IslandsEffectUI):
        islands_ui.apply_clicked.connect(self._on_apply_clicked)

    def _on_apply_clicked(self):
        if not self.is_active():
            return
        if self._typed_state.data.mode == IslandsSegmentationMode.KEEP_LARGEST_ISLAND:
            self.effect.keep_largest_island()
        elif self._typed_state.data.mode == IslandsSegmentationMode.REMOVE_SMALL_ISLANDS:
            self.effect.remove_small_islands(self._typed_state.data.minimum_size)
        elif self._typed_state.data.mode == IslandsSegmentationMode.SPLIT_TO_SEGMENTS:
            self.effect.split_islands_to_segments()
