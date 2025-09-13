from __future__ import annotations

import math
from enum import Enum, auto

from vtkmodules.vtkCommonMath import vtkMatrix4x4

from trame_slicer.views import SliceView

from .brush_model import BrushModel, BrushShape
from .segmentation_paint_widget import SegmentationPaintWidget


class BrushScaleMode(Enum):
    Absolute = auto()
    ScreenInvariant = auto()


class SegmentationPaintWidget2D(SegmentationPaintWidget):
    def __init__(self, view: SliceView):
        super().__init__(BrushModel(BrushShape.Cylinder))
        self._brush_scale_mode = BrushScaleMode.ScreenInvariant
        self._view = view
        relative_brush_size = 5
        self._brush_diameter_pix = (relative_brush_size / 100) * self._vertical_screen_size()

    @property
    def brush_diameter_pix(self):
        if self._brush_scale_mode == BrushScaleMode.ScreenInvariant:
            return self._brush_diameter_pix

        return self._compute_brush_pixel_diameter_from_absolute(self._brush_diameter_pix)

    def _get_mm_per_pixel(self):
        xy_to_slice: vtkMatrix4x4 = self._view.mrml_view_node.GetXYToSlice()
        return math.sqrt(sum([xy_to_slice.GetElement(i, 1) ** 2 for i in range(3)]))

    def _compute_brush_pixel_diameter_from_absolute(self, brush_diameter_mm):
        mm_per_pixel = self._get_mm_per_pixel()
        if mm_per_pixel == 0:
            return brush_diameter_mm

        return brush_diameter_mm / mm_per_pixel

    def _vertical_screen_size(self):
        return self._view.render_window().GetScreenSize()[1]

    def update_brush_diameter(self) -> None:
        self._brush_model.set_cylinder_parameters(
            radius=self.brush_diameter_pix / 2.0,
            resolution=32,
            height=self._view.get_slice_step() / 2.0,
        )

    def update_widget_position(self, world_pos: list[float]) -> None:
        self.update_brush_diameter()
        xy_to_ras: vtkMatrix4x4 = self._view.mrml_view_node.GetXYToRAS()
        self._update_brush_position(world_pos, xy_to_ras)
        if self.is_painting():
            self.add_point_to_selection(world_pos)

    def _update_brush_position(self, world_pos: list[float], xy_to_ras: vtkMatrix4x4) -> None:
        self._brush_model.set_shape(BrushShape.Cylinder)

        # brush is rotated to the slice widget plane
        brush_to_world_origin_transform_matrix = vtkMatrix4x4()
        brush_to_world_origin_transform_matrix.DeepCopy(xy_to_ras)
        brush_to_world_origin_transform_matrix.SetElement(0, 3, 0)
        brush_to_world_origin_transform_matrix.SetElement(1, 3, 0)
        brush_to_world_origin_transform_matrix.SetElement(2, 3, 0)

        # cylinder's long axis is the Y axis, we need to rotate it to Z axis
        self._brush_model.brush_to_world_origin_transform.Identity()
        self._brush_model.brush_to_world_origin_transform.Concatenate(brush_to_world_origin_transform_matrix)
        self._brush_model.brush_to_world_origin_transform.RotateX(90)

        self._brush_model.world_origin_to_world_transform.Identity()
        self._brush_model.world_origin_to_world_transform.Translate(world_pos[:3])
