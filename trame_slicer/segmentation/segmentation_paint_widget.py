from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkCommonExecutionModel import vtkAlgorithmOutput
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkFiltersCore import vtkGlyph3D

from trame_slicer.views import SliceView, ThreeDView

from .brush_source import BrushSource
from .paint_effect_parameters import (
    BrushDiameterMode,
    BrushShape,
    PaintEffectParameters,
)
from .segment_modifier import SegmentModifier

T = TypeVar("T")


class SegmentationPaintWidget(Generic[T], ABC):
    def __init__(self, view: T) -> None:
        super().__init__()

        self._view: T = view
        self._brush_model = BrushSource(BrushShape.Sphere)
        self._paint_coordinates_world = vtkPoints()
        self._paint_coordinates_polydata = vtkPolyData()
        self._paint_coordinates_polydata.SetPoints(self._paint_coordinates_world)

        self._painting = False
        self._modifier: SegmentModifier | None = None
        self._feedback_glyph = vtkGlyph3D()
        self._feedback_glyph.SetSourceConnection(self._brush_model.get_untransformed_output_port())
        self._feedback_glyph.SetInputData(self._paint_coordinates_polydata)

        self._params = PaintEffectParameters()
        self._stroke_rel_spacing = 0.1

    def _vertical_screen_size_pix(self):
        return self._view.render_window().GetScreenSize()[1]

    def _view_height_pix(self):
        return self._view.render_window().GetSize()[1]

    def get_brush_polydata_port(self) -> vtkAlgorithmOutput:
        return self._brush_model.get_transformed_polydata_output_port()

    def get_feedback_polydata_port(self):
        return self._feedback_glyph.GetOutputPort()

    def set_modifier(self, modifier: SegmentModifier | None):
        self._modifier = modifier

    def _add_point_to_selection(self, position: list[float]) -> None:
        self._paint_coordinates_world.InsertNextPoint(position)

    def _modified(self):
        self._paint_coordinates_world.Modified()
        self._paint_coordinates_polydata.Modified()
        self._feedback_glyph.Modified()

    def start_painting(self) -> None:
        self._painting = True

    def stop_painting(self) -> None:
        self._painting = False
        if self._paint_coordinates_world.GetNumberOfPoints() > 0:
            self._commit()

    def is_painting(self) -> bool:
        return self._painting

    def _commit(self) -> None:
        try:
            algo = self._brush_model.get_untransformed_output_port().GetProducer()
            algo.Update()
            self._modifier.apply_glyph(algo.GetOutput(), self._paint_coordinates_world)
        finally:
            # ensure points are always cleared
            self._paint_coordinates_world.SetNumberOfPoints(0)
            self._feedback_glyph.Modified()

    def _convert_relative_brush_diameter_to_mm(self, rel_diameter):
        return (rel_diameter / 100) * self._vertical_screen_size_pix() * self._get_view_mm_per_pix()

    def _update_brush_size(self):
        diameter = self._params.brush_diameter
        if self._params.brush_diameter_mode == BrushDiameterMode.ScreenRelative:
            diameter = self._convert_relative_brush_diameter_to_mm(diameter)

        self._brush_model.set_diameter(diameter)

    def update_widget_position(self, position):
        if self.is_painting():
            self._interpolate_brush_position_if_needed(position)
            self._add_point_to_selection(position)
        else:
            self._update_brush()

        self._brush_model.set_brush_to_world_position(position)
        self._modified()

    def _update_brush(self):
        self._update_brush_shape()
        self._update_brush_size()

    def _has_paint_coordinates(self) -> bool:
        return self._paint_coordinates_world.GetNumberOfPoints() > 0

    def _get_last_paint_coordinate(self) -> list[float] | None:
        if self._has_paint_coordinates():
            return list(self._paint_coordinates_world.GetPoint(self._paint_coordinates_world.GetNumberOfPoints() - 1))
        return None

    def _interpolate_brush_position_if_needed(self, position):
        if not self._has_paint_coordinates():
            return

        maximum_distance_between_points = self._stroke_rel_spacing * self._brush_model.get_diameter()
        if maximum_distance_between_points <= 0.0:
            return

        last_paint_position = self._get_last_paint_coordinate()
        stroke_length = math.dist(position, last_paint_position)
        n_points_to_add = int(stroke_length / maximum_distance_between_points) + 1

        for i_pt in range(1, n_points_to_add):
            weight = i_pt / n_points_to_add
            interpolated = [weight * last_paint_position[i] + (1.0 - weight) * position[i] for i in range(3)]
            self._add_point_to_selection(interpolated)

    def update_paint_parameters(self, params: PaintEffectParameters):
        self._params = params
        self._update_brush()

    @abstractmethod
    def _get_view_mm_per_pix(self):
        raise NotImplementedError()

    @abstractmethod
    def _update_brush_shape(self):
        raise NotImplementedError()


class SegmentationPaintWidget2D(SegmentationPaintWidget[SliceView]):
    def _get_view_mm_per_pix(self):
        view_node = self._view.get_view_node()
        if not view_node:
            return 1

        xy_to_slice: vtkMatrix4x4 = view_node.GetXYToSlice()
        return math.sqrt(sum([xy_to_slice.GetElement(i, 1) ** 2 for i in range(3)]))

    def _update_brush_shape(self) -> None:
        if self._params.use_sphere_brush:
            self._brush_model.set_shape(BrushShape.Sphere)
        else:
            view_node = self._view.get_view_node()
            if not view_node:
                return

            slice_to_ras: vtkMatrix4x4 = view_node.GetSliceToRAS()
            self._brush_model.set_shape(BrushShape.Cylinder)
            self._brush_model.set_brush_rotation(slice_to_ras)
            self._brush_model.set_cylinder_height(self._view.get_slice_step() / 2.0)


class SegmentationPaintWidget3D(SegmentationPaintWidget[ThreeDView]):
    def _update_brush_shape(self):
        self._brush_model.set_shape(BrushShape.Sphere)

    def _get_view_mm_per_pix(self):
        camera = self._view.renderer().GetActiveCamera()
        if camera.GetParallelProjection():
            return (camera.GetParallelScale() * 2.0) / self._view_height_pix()

        # Compute view height in mm given camera distance and view angle
        heightMm = 2.0 * camera.GetDistance() * math.tan(math.radians(camera.GetViewAngle()) / 2)
        return heightMm / self._view_height_pix()
