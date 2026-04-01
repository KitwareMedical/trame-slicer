from trame_server import Server
from trame_server.utils.typed_state import TypedState

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import SegmentationEffectSmoothing

from ...ui import (
    BrushParametersState,
    SegmentEditorUI,
    SmoothingEffectMode,
    SmoothingEffectUI,
    SmoothingState,
)
from .brush_effect_logic import BrushEffectLogic


class SmoothingEffectLogic(BrushEffectLogic[SmoothingState, SegmentationEffectSmoothing]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SmoothingState, SegmentationEffectSmoothing)

    @property
    def _brush_state(self) -> TypedState[BrushParametersState]:
        """Typed state or substate holding the brush parameters"""
        return self._typed_state.get_sub_state(self._typed_state.name.brush)

    def set_ui(self, ui: SegmentEditorUI):
        self.set_effect_ui(ui.get_effect_ui(SegmentationEffectSmoothing))
        self.bind_changes(
            {
                self.name.mode: self.set_smoothing_mode,
                self.name.kernel_size: self.set_kernel_size,
                self.name.standard_deviation: self.set_standard_deviation,
                self.name.smoothing_factor: self.set_joint_smoothing_factor,
            }
        )

    def set_effect_ui(self, smoothing_ui: SmoothingEffectUI):
        smoothing_ui.apply_clicked.connect(self._on_apply_clicked)

    def set_smoothing_mode(self, mode: SmoothingEffectMode):
        if not self.is_active():
            return
        self.effect.set_smoothing_mode(mode)

    def set_kernel_size(self, kernel_size: float):
        if not self.is_active():
            return
        self.effect.set_kernel_size(kernel_size)

    def set_standard_deviation(self, standard_deviation: float):
        if not self.is_active():
            return
        self.effect.set_standard_deviation(standard_deviation)

    def set_joint_smoothing_factor(self, smoothing_factor: float):
        if not self.is_active():
            return
        self.effect.set_joint_smoothing_factor(smoothing_factor)

    def _on_apply_clicked(self):
        if not self.is_active():
            return
        self.effect.apply_smoothing()

    def _on_effect_changed(self, _effect_name) -> None:
        super()._on_effect_changed(_effect_name)
        self.set_kernel_size(self.data.kernel_size)
        self.set_standard_deviation(self.data.standard_deviation)
        self.set_joint_smoothing_factor(self.data.smoothing_factor)
        self._refresh_brush()
