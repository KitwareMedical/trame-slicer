from typing import Generic, TypeVar

from trame_server import Server
from trame_server.utils.typed_state import TypedState

from trame_slicer.core import SlicerApp

from ...ui import BrushParametersState, SegmentEditorUI
from .base_segmentation_logic import BaseEffectLogic, T, U

TBrush = TypeVar("TBrush", bound=BrushParametersState)


class BrushEffectLogic(BaseEffectLogic[TBrush, U], Generic[TBrush, U]):
    def __init__(self, server: Server, slicer_app: SlicerApp, state_type: type[T], effect_type: type[U]):
        super().__init__(server, slicer_app, state_type, effect_type)
        self.bind_changes({self._brush_state.name: self._on_brush_params_changed})

        self.effect.parameters_changed.connect(self._on_modified_event)

    @property
    def _brush_state(self) -> TypedState[BrushParametersState]:
        """Typed state or substate holding the brush parameters"""
        return self._typed_state

    @property
    def _is_brush_diameter_sync(self) -> bool:
        """Check that diameter is synchronized between trame and slicer"""
        return self.effect.get_brush_diameter() == self._brush_state.data.brush_diameter_slider.value

    @property
    def _is_sphere_brush_sync(self) -> bool:
        """Check that sphere brush is synchronized between trame and slicer"""
        return self.effect.is_sphere_brush() == self._brush_state.data.use_sphere_brush

    def set_ui(self, ui: SegmentEditorUI):
        pass

    def _on_brush_params_changed(self, *_args):
        self._refresh_brush()

    def _refresh_brush(self):
        with self.effect.parameters_changed.emit_blocked():
            if not self._is_brush_diameter_sync:
                self.effect.set_brush_diameter(
                    self._brush_state.data.brush_diameter_slider.value, self._brush_state.data.brush_diameter_mode
                )
            if not self._is_sphere_brush_sync:
                self.effect.set_use_sphere_brush(self._brush_state.data.use_sphere_brush)

    def _on_effect_changed(self, _effect_name: str) -> None:
        if not self.is_active():
            return
        self._refresh_brush()

    def _on_modified_event(self):
        if not self.is_active():
            return

        if self._is_brush_diameter_sync:
            return

        # React to brush size change
        limited_value = min(
            max(self.effect.get_brush_diameter(), self._brush_state.data.brush_diameter_slider.min_value),
            self._brush_state.data.brush_diameter_slider.max_value,
        )
        self._brush_state.data.brush_diameter_slider.value = limited_value
        self.effect.set_brush_diameter(limited_value, self._brush_state.data.brush_diameter_mode)
