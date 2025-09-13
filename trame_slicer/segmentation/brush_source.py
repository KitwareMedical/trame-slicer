from __future__ import annotations

from vtkmodules.vtkCommonExecutionModel import vtkAlgorithmOutput
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkFiltersSources import vtkCylinderSource, vtkSphereSource

from .paint_effect_parameters import BrushShape


class BrushSource:
    def __init__(self, shape: BrushShape, diameter: float = 16.0, cylinder_height: float = 1.0) -> None:
        self._sphere_source = vtkSphereSource()
        self._sphere_source.SetPhiResolution(16)
        self._sphere_source.SetThetaResolution(16)

        self._cylinder_source = vtkCylinderSource()
        self._cylinder_source.SetResolution(32)

        self._brush_to_world_origin_transform = vtkTransform()
        self._brush_to_world_origin_transformer = vtkTransformPolyDataFilter()
        self._brush_to_world_origin_transformer.SetTransform(self._brush_to_world_origin_transform)

        self._brush_poly_data_normals = vtkPolyDataNormals()
        self._brush_poly_data_normals.SetInputConnection(self._brush_to_world_origin_transformer.GetOutputPort())
        self._brush_poly_data_normals.AutoOrientNormalsOn()

        self._world_origin_to_world_transform = vtkTransform()
        self._transformed_polydata_filter = vtkTransformPolyDataFilter()
        self._transformed_polydata_filter.SetTransform(self._world_origin_to_world_transform)
        self._transformed_polydata_filter.SetInputConnection(self._brush_poly_data_normals.GetOutputPort())

        self._shape = None  # force shape update
        self.set_diameter(diameter)
        self.set_shape(shape)
        self.set_cylinder_height(cylinder_height)

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
        shape_source = self._sphere_source if self._shape == BrushShape.Sphere else self._cylinder_source
        self._brush_to_world_origin_transformer.SetInputConnection(shape_source.GetOutputPort())

    def get_diameter(self):
        return self._cylinder_source.GetRadius() * 2.0

    def set_diameter(self, diameter: float):
        radius = diameter / 2.0
        self._sphere_source.SetRadius(radius)
        self._cylinder_source.SetRadius(radius)

    def set_cylinder_height(self, cylinder_height: float):
        self._cylinder_source.SetHeight(cylinder_height)

    def get_transformed_polydata_output_port(self) -> vtkAlgorithmOutput:
        """
        Return the output port of transformed brush model
        """
        return self._transformed_polydata_filter.GetOutputPort()

    def get_untransformed_output_port(self) -> vtkAlgorithmOutput:
        """
        Return the output port of untransformed brush model
        Useful for feedback actors
        """
        return self._brush_poly_data_normals.GetOutputPort()

    def set_brush_rotation(self, slice_to_ras: vtkMatrix4x4):
        # brush is rotated to the slice widget plane
        brush_to_world_origin_transform_matrix = vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                brush_to_world_origin_transform_matrix.SetElement(i, j, slice_to_ras.GetElement(i, j))

        # cylinder's long axis is the Y axis, we need to rotate it to Z axis
        self.brush_to_world_origin_transform.Identity()
        self.brush_to_world_origin_transform.Concatenate(brush_to_world_origin_transform_matrix)
        self.brush_to_world_origin_transform.RotateX(90)

    def set_brush_to_world_position(self, world_pos):
        self.world_origin_to_world_transform.Identity()
        self.world_origin_to_world_transform.Translate(world_pos[:3])
        self._transformed_polydata_filter.Modified()
