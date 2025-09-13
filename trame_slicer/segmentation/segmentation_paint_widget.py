from __future__ import annotations

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkFiltersCore import vtkGlyph3D

from .brush_model import BrushModel
from .segment_modifier import SegmentModifier


class SegmentationPaintWidget:
    def __init__(self, brush_model: BrushModel) -> None:
        super().__init__()

        self._brush_model = brush_model
        self._paint_coordinates_world = vtkPoints()
        self._paint_coordinates_polydata = vtkPolyData()
        self._paint_coordinates_polydata.SetPoints(self._paint_coordinates_world)

        self._painting = False
        self._modifier: SegmentModifier | None = None
        self._feedback_glyph = vtkGlyph3D()
        self._feedback_glyph.SetSourceConnection(self._brush_model.get_untransformed_output_port())
        self._feedback_glyph.SetInputData(self._paint_coordinates_polydata)

    def get_brush_polydata(self) -> vtkPolyData:
        return self._brush_model.get_polydata()

    def get_feedback_polydata(self):
        self._feedback_glyph.Update()
        return self._feedback_glyph.GetOutput()

    def set_modifier(self, modifier: SegmentModifier | None):
        self._modifier = modifier

    @property
    def paint_coordinates_world(self) -> vtkPoints:
        return self._paint_coordinates_world

    def add_point_to_selection(self, position: list[float]) -> None:
        self._paint_coordinates_world.InsertNextPoint(position)
        self._paint_coordinates_world.Modified()

    def start_painting(self) -> None:
        self._painting = True

    def stop_painting(self) -> None:
        self._painting = False
        if self._paint_coordinates_world.GetNumberOfPoints() > 0:
            self.commit()

    def is_painting(self) -> bool:
        return self._painting

    def commit(self) -> None:
        try:
            algo = self._brush_model.get_untransformed_output_port().GetProducer()
            algo.Update()
            self._modifier.apply_glyph(algo.GetOutput(), self._paint_coordinates_world)
        finally:
            # ensure points are always cleared
            self._paint_coordinates_world.SetNumberOfPoints(0)

    def update_widget_position(self, position):
        raise NotImplementedError()

    def invalidate_last_position(self):
        pass
