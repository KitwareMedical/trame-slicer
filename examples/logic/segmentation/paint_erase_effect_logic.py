from typing import Generic

from trame_server import Server

from examples.ui import PaintEffectState, SegmentEditorUI
from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import (
    SegmentationEffectErase,
    SegmentationEffectPaint,
    SegmentationEffectPaintErase,
)

from .base_segmentation_logic import BaseEffectLogic, U


class PaintEraseEffectLogic(BaseEffectLogic[PaintEffectState, U], Generic[U]):
    def __init__(self, server: Server, slicer_app: SlicerApp, effect_type: type[U]):
        super().__init__(server, slicer_app, PaintEffectState, effect_type)
        self.bind_changes(
            {
                self.name.use_sphere_brush: self._on_brush_type_changed,
                self.name.brush_diameter_slider.value: self._on_brush_size_changed,
                self.name.brush_diameter_mode: self._on_brush_diameter_mode_changed,
            }
        )

    @property
    def effect(self) -> SegmentationEffectPaintErase:
        return super().effect

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


class PaintEffectLogic(PaintEraseEffectLogic[SegmentationEffectPaint]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentationEffectPaint)


class EraseEffectLogic(PaintEraseEffectLogic[SegmentationEffectErase]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentationEffectErase)
