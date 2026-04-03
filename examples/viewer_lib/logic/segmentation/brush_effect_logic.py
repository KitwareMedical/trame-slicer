from typing import Generic, TypeVar

from trame_server import Server

from trame_slicer.core import SlicerApp

from ...ui import BrushParametersState, SegmentEditorUI
from .base_segmentation_logic import BaseEffectLogic, T, U

TBrush = TypeVar("TBrush", bound=BrushParametersState)


class BrushEffectLogic(BaseEffectLogic[TBrush, U], Generic[TBrush, U]):
    def __init__(self, server: Server, slicer_app: SlicerApp, state_type: type[T], effect_type: type[U]):
        super().__init__(server, slicer_app, state_type, effect_type)
        self.bind_changes(
            {
                self.name.use_sphere_brush: self._on_brush_type_changed,
                self.name.brush_diameter_slider.value: self._on_brush_size_changed,
                self.name.brush_diameter_mode: self._on_brush_diameter_mode_changed,
            }
        )

    def set_ui(self, ui: SegmentEditorUI):
        pass

    def _on_brush_type_changed(self, _use_sphere_brush):
        self._refresh_brush()

    def _on_brush_size_changed(self, _diameter):
        self._refresh_brush()

    def _on_brush_diameter_mode_changed(self, _mode):
        self._refresh_brush()

    def _refresh_brush(self):
        if not self.is_active():
            return
        self.effect.set_brush_diameter(self.data.brush_diameter_slider.value, self.data.brush_diameter_mode)
        self.effect.set_use_sphere_brush(self.data.use_sphere_brush)

    def _on_effect_changed(self, _effect_name: str) -> None:
        self._refresh_brush()
        self.effect.parameters_changed.connect(self._on_modified_event)

    def _on_modified_event(self):
        if not self.is_active():
            return
        slicer_brush_size = self.effect.get_brush_diameter()
        trame_brush_size = self.data.brush_diameter_slider.value
        if trame_brush_size == slicer_brush_size:
            return
        # React to brush size change
        limited_value = min(
            max(slicer_brush_size, self.data.brush_diameter_slider.min_value),
            self.data.brush_diameter_slider.max_value,
        )
        self.data.brush_diameter_slider.value = limited_value
        self.effect.set_brush_diameter(limited_value)
