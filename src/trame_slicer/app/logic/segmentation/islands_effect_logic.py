from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import SegmentationEffectIslands, SegmentationIslandsMode

from ...ui import (
    IslandsEffectUI,
    IslandsState,
    SegmentEditorUI,
)
from .base_segmentation_logic import BaseEffectLogic


class IslandsEffectLogic(BaseEffectLogic[IslandsState, SegmentationEffectIslands]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, IslandsState, SegmentationEffectIslands)

        self.bind_changes(
            {
                self.name.mode: self._set_mode,
                self.name.minimum_size: self._set_minimum_island_size,
            }
        )

    def set_ui(self, ui: SegmentEditorUI) -> None:
        self.set_effect_ui(ui.get_effect_ui(SegmentationEffectIslands))

    def set_effect_ui(self, islands_ui: IslandsEffectUI) -> None:
        islands_ui.apply_clicked.connect(self._on_apply_clicked)

    def _set_mode(self, island_segmentation_mode: SegmentationIslandsMode) -> None:
        if not self.is_active():
            return
        self.effect.set_island_mode(island_segmentation_mode)

    def _set_minimum_island_size(self, minimum_island_size: int) -> None:
        if not self.is_active():
            return
        self.effect.set_minimum_island_size(minimum_island_size)

    def _on_apply_clicked(self) -> None:
        if not self.is_active():
            return
        self.effect.apply()

    def _on_effect_parameters_changed(self) -> None:
        with self.state:
            self.data.mode = self.effect.get_island_mode()
            self.data.minimum_size = self.effect.get_minimum_island_size()

    def _on_effect_changed(self, _effect_name: str) -> None:
        if not self.is_active():
            return
        self.effect.parameters_changed.connect(self._on_effect_parameters_changed)
