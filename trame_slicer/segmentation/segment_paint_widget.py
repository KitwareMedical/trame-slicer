from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonExecutionModel import vtkAlgorithmOutput
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkFiltersSources import vtkCylinderSource, vtkSphereSource
from vtkmodules.vtkRenderingCore import vtkProp

from trame_slicer.views import AbstractView, AbstractViewInteractor

from .segment_modifier import SegmentModifier
from .segmentation_widget import SegmentationWidget


class BrushShape(IntEnum):
    Sphere = 0
    Cylinder = 1


class BrushModel:
    def __init__(self, shape: BrushShape) -> None:
        self._sphere_source = vtkSphereSource()
        self._sphere_source.SetPhiResolution(16)
        self._sphere_source.SetThetaResolution(16)
        self._sphere_source.SetRadius(8.0)

        self._cylinder_source = vtkCylinderSource()
        self._cylinder_source.SetResolution(32)
        self._cylinder_source.SetRadius(8.0)
        self._cylinder_source.SetHeight(1.0)

        self._brush_to_world_origin_transform = vtkTransform()
        self._brush_to_world_origin_transformer = vtkTransformPolyDataFilter()
        self._brush_to_world_origin_transformer.SetTransform(self._brush_to_world_origin_transform)

        self._brush_poly_data_normals = vtkPolyDataNormals()
        self._brush_poly_data_normals.SetInputConnection(self._brush_to_world_origin_transformer.GetOutputPort())
        self._brush_poly_data_normals.AutoOrientNormalsOn()

        self._world_origin_to_world_transform = vtkTransform()
        self._world_origin_to_world_transformer = vtkTransformPolyDataFilter()
        self._world_origin_to_world_transformer.SetTransform(self._world_origin_to_world_transform)
        self._world_origin_to_world_transformer.SetInputConnection(self._brush_poly_data_normals.GetOutputPort())

        self._shape = None  # force shape update
        self.set_shape(shape)

    @property
    def brush_to_world_origin_transform(self) -> vtkTransform:
        return self._brush_to_world_origin_transform

    @property
    def world_origin_to_world_transform(self) -> vtkTransform:
        return self._world_origin_to_world_transform

    def set_shape(self, shape: BrushShape) -> None:
        if self._shape == shape:
            return

        self._shape = shape
        self._brush_to_world_origin_transform.Identity()
        if shape == BrushShape.Sphere:
            self._brush_to_world_origin_transformer.SetInputConnection(self._sphere_source.GetOutputPort())
        elif shape == BrushShape.Cylinder:
            self._brush_to_world_origin_transformer.SetInputConnection(self._cylinder_source.GetOutputPort())
        else:
            _error_msg = f"Invalid shape value {shape}"
            raise Exception(_error_msg)

    def set_sphere_parameters(self, radius: float, phi_resolution: int, theta_resolution: int):
        self._sphere_source.SetPhiResolution(phi_resolution)
        self._sphere_source.SetThetaResolution(theta_resolution)
        self._sphere_source.SetRadius(radius)

    def set_cylinder_parameters(self, *, radius: float, resolution: int, height: float):
        self._cylinder_source.SetResolution(resolution)
        self._cylinder_source.SetHeight(height)
        self._cylinder_source.SetRadius(radius)

    def get_output_port(self) -> vtkAlgorithmOutput:
        """
        Return the output port of transformed brush model
        """
        return self._world_origin_to_world_transformer.GetOutputPort()

    def get_untransformed_output_port(self) -> vtkAlgorithmOutput:
        """
        Return the output port of untransformed brush model
        Useful for feedback actors
        """
        return self._brush_poly_data_normals.GetOutputPort()


class AbstractBrush(ABC):
    @abstractmethod
    def get_prop(self) -> vtkProp:
        raise NotImplementedError()

    def get_visibility(self) -> bool:
        return self.get_prop().GetVisibility() != 0

    def set_visibility(self, visibility: bool) -> None:
        return self.get_prop().SetVisibility(int(visibility))


class SegmentPaintWidget(SegmentationWidget):
    def __init__(
        self,
        view: AbstractView,
        modifier: SegmentModifier,
        brush_model: BrushModel,
        brush: AbstractBrush,
        brush_feedback: AbstractBrush,
    ) -> None:
        super().__init__(modifier)
        self._view = view
        self._brush_model = brush_model
        self._brush = brush
        self._brush_feedback = brush_feedback
        self._brush_enabled = False
        self._paint_coordinates_world = vtkPoints()
        self._painting = False

    @property
    def paint_coordinates_world(self) -> vtkPoints:
        return self._paint_coordinates_world

    def add_point_to_selection(self, position: list[float]) -> None:
        self._paint_coordinates_world.InsertNextPoint(position)
        self._paint_coordinates_world.Modified()

    def enable_brush(self) -> None:
        self._brush.set_visibility(True)
        self._brush_enabled = True
        renderer = self._view.renderer()
        renderer.AddViewProp(self._brush.get_prop())
        renderer.AddViewProp(self._brush_feedback.get_prop())

    def disable_brush(self) -> None:
        if self.is_painting():
            self.stop_painting()
        self._brush.set_visibility(False)
        self._brush_enabled = False
        renderer = self._view.renderer()
        renderer.RemoveViewProp(self._brush.get_prop())
        renderer.RemoveViewProp(self._brush_feedback.get_prop())

    def is_brush_enabled(self) -> bool:
        return self._brush_enabled

    def start_painting(self) -> None:
        self._brush_feedback.set_visibility(True)
        self._painting = True

    def stop_painting(self) -> None:
        self._brush_feedback.set_visibility(False)
        self._painting = False
        if self._paint_coordinates_world.GetNumberOfPoints() > 0:
            self.commit()

    def is_painting(self) -> bool:
        return self._painting

    def commit(self) -> None:
        try:
            algo = self._brush_model.get_untransformed_output_port().GetProducer()
            algo.Update()
            self.modifier.apply_glyph(algo.GetOutput(), self._paint_coordinates_world)
        finally:
            # ensure points are always cleared
            self._paint_coordinates_world.SetNumberOfPoints(0)


class SegmentPaintWidgetInteractor(AbstractViewInteractor):
    def __init__(self, widget: SegmentPaintWidget) -> None:
        super().__init__()
        self._widget = widget

    @property
    def widget(self) -> SegmentPaintWidget:
        return self._widget
