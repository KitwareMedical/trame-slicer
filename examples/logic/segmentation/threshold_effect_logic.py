from trame_server import Server

from examples.ui import SegmentEditorUI, ThresholdEffectUI, ThresholdState
from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import SegmentationEffectThreshold

from .base_segmentation_logic import BaseEffectLogic


class ThresholdEffectLogic(BaseEffectLogic[ThresholdState, SegmentationEffectThreshold]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, ThresholdState, SegmentationEffectThreshold)
        self.bind_changes({self.name.threshold_slider.value: self._on_threshold_changed})

    def set_ui(self, ui: SegmentEditorUI):
        self.set_effect_ui(ui.get_effect_ui(SegmentationEffectThreshold))

    def set_effect_ui(self, threshold_ui: ThresholdEffectUI):
        threshold_ui.auto_threshold_clicked.connect(self._on_auto_threshold_clicked)
        threshold_ui.apply_clicked.connect(self._on_apply_threshold_clicked)

    def _on_auto_threshold_clicked(self):
        if not self.is_active():
            return
        self.effect.auto_threshold()
        self.data.threshold_slider.value = list(self.effect.get_threshold_min_max_values())

    def _on_apply_threshold_clicked(self):
        if not self.is_active():
            return
        self.effect.apply()
        self.segmentation_editor.deactivate_effect()

    def _on_threshold_changed(self, value: tuple[float, float]) -> None:
        if not self.is_active():
            return
        self.effect.set_threshold_min_max_values(value)

    def _on_effect_changed(self, _effect_name):
        if not self.is_active():
            return

        volume_node = self.segmentation_editor.active_volume_node
        if not volume_node:
            return

        min_val, max_val = volume_node.GetImageData().GetScalarRange()
        self.data.threshold_slider.min_value = min_val
        self.data.threshold_slider.max_value = max_val
        self._on_auto_threshold_clicked()
