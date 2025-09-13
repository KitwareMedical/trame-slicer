from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from slicer import vtkMRMLModelNode
from vtkmodules.vtkCommonExecutionModel import vtkAlgorithmOutput
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkFiltersSources import vtkCylinderSource, vtkSphereSource


class BrushShape(IntEnum):
    Sphere = 0
    Cylinder = 1


@dataclass
class PaintEffectParameters:
    brush_radius: float = 5.0
    brush_shape: BrushShape = BrushShape.Cylinder
    brush_model_node: vtkMRMLModelNode | None = None
    paint_feedback_model_node: vtkMRMLModelNode | None = None


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

    def get_polydata(self):
        """
        Return the transformed polydata of the brush model.
        """
        self._world_origin_to_world_transformer.Update()
        return self._world_origin_to_world_transformer.GetOutput()

    def get_untransformed_output_port(self) -> vtkAlgorithmOutput:
        """
        Return the output port of untransformed brush model
        Useful for feedback actors
        """
        return self._brush_poly_data_normals.GetOutputPort()
