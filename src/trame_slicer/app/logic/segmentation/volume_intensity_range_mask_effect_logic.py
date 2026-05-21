from trame_server import Server
from trame_server.utils.typed_state import TypedState

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import SegmentationEffectVolumeIntensityMask

from ...ui import SegmentEditorUI, ThresholdState, VolumeIntensityRangeMaskState
from .base_segmentation_logic import BaseEffectLogic


class VolumeIntensityRangeMaskEffectLogic(
    BaseEffectLogic[VolumeIntensityRangeMaskState, SegmentationEffectVolumeIntensityMask]
):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, VolumeIntensityRangeMaskState, SegmentationEffectVolumeIntensityMask)
        self.segmentation_editor.editor_node_modified.connect(self._refresh_trame_state)
        self.effect.parameters_changed.connect(self._refresh_trame_state)

        self.bind_changes(
            {
                self.name.threshold_slider.value: self._on_threshold_changed,
                self.name.is_visible: self.effect.set_mask_visible,
                self.name.is_enabled: self.effect.set_mask_enabled,
            }
        )

        self.threshold_state = TypedState(self.state, ThresholdState)
        self.threshold_state.bind_changes(
            {
                self.threshold_state.name.threshold_slider.min_value: self._on_threshold_range_changed,
                self.threshold_state.name.threshold_slider.max_value: self._on_threshold_range_changed,
            }
        )

    def _on_threshold_changed(self, value: tuple[float, float]) -> None:
        self.effect.set_mask_range(*value)

    def set_ui(self, ui: SegmentEditorUI):
        pass

    def _refresh_trame_state(self, *_):
        self.data.threshold_slider.value = list(self.effect.get_mask_range())
        self.data.is_enabled = self.effect.is_mask_enabled()
        self.data.is_visible = self.effect.is_visible

    def _on_threshold_range_changed(self, *_):
        self.data.threshold_slider.min_value = self.threshold_state.data.threshold_slider.min_value
        self.data.threshold_slider.max_value = self.threshold_state.data.threshold_slider.max_value
