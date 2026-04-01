from __future__ import annotations

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData

from .abstract_segmentation_effect_brush import AbstractSegmentationEffectBrush
from .segment_modifier import ModificationMode


class SegmentationEffectPaintErase(AbstractSegmentationEffectBrush):
    def paint_glyph_at_world_coordinates(self, polydata: vtkPolyData, paint_coordinates_world: vtkPoints):
        self._modifier.apply_glyph(polydata, paint_coordinates_world)


class SegmentationEffectPaint(SegmentationEffectPaintErase):
    def __init__(self) -> None:
        super().__init__(ModificationMode.Add)


class SegmentationEffectErase(SegmentationEffectPaintErase):
    def __init__(self) -> None:
        super().__init__(ModificationMode.Remove)
