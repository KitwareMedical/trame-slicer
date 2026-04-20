from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLNode,
    vtkMRMLSliceNode,
    vtkMRMLTransformNode,
    vtkOrientedImageData,
    vtkOrientedImageDataResample,
)
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkQuad
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals, vtkTriangleFilter
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter
from vtkmodules.vtkFiltersModeling import vtkFillHolesFilter
from vtkmodules.vtkFiltersSources import vtkCubeSource
from vtkmodules.vtkImagingCore import vtkImageStencilData
from vtkmodules.vtkImagingStencil import (
    vtkImageStencilToImage,
    vtkPolyDataToImageStencil,
)
from vtkmodules.vtkRenderingCore import vtkCoordinate, vtkRenderer

from ..utils import vtk_image_to_np
from ..views import AbstractView
from .scissors_effect_parameters import (
    BrushInteractionMode,
    ScissorsEffectFillMode,
    ScissorsEffectRangeMode,
)
from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline


class SegmentationEffectScissors(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()

        self._brush_interaction_mode: BrushInteractionMode = BrushInteractionMode.CONTINUOUS
        self._range_mode: ScissorsEffectRangeMode = ScissorsEffectRangeMode.UNLIMITED
        self._fill_mode: ScissorsEffectFillMode = ScissorsEffectFillMode.ERASE_INSIDE
        self._symmetric_distance: float = 0.0

    @property
    def brush_interaction_mode(self) -> BrushInteractionMode:
        return self._brush_interaction_mode

    def _create_pipeline(
        self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        from .segmentation_effect_scissors_widget import SegmentationScissorsPipeline

        return SegmentationScissorsPipeline()

    def set_brush_interaction_mode(self, mode: BrushInteractionMode):
        self._brush_interaction_mode = mode

    def set_symmetric_distance(self, symmetric_distance: float):
        self._symmetric_distance = symmetric_distance

    def set_fill_mode(self, fill_mode: ScissorsEffectFillMode):
        self._fill_mode = fill_mode

    def set_range_mode(self, range_mode: ScissorsEffectRangeMode):
        self._range_mode = range_mode

    @staticmethod
    def _close_polydata(polydata: vtkPolyData) -> vtkPolyData:
        """Fill any open boundary loops to produce a watertight surface."""
        filler = vtkFillHolesFilter()
        filler.SetInputData(polydata)
        filler.SetHoleSize(1e10)  # large enough to catch any hole
        filler.Update()

        # Ensure normals are consistent after filling
        normals = vtkPolyDataNormals()
        normals.SetInputConnection(filler.GetOutputPort())
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.Update()

        return normals.GetOutput()

    def _stencil_polydata_from_display_coordinates(self, points_display: vtkPoints, view: AbstractView) -> vtkPolyData:
        view_node = view.get_view_node()
        renderer = view.first_renderer()

        point_count = points_display.GetNumberOfPoints()

        polydata = vtkPolyData()
        points = vtkPoints()
        points.SetNumberOfPoints(2 * point_count)
        polydata.SetPoints(points)
        cells = vtkCellArray()
        polydata.SetPolys(cells)

        quad = vtkQuad()
        ids = quad.GetPointIds()
        ids.SetNumberOfIds(4)

        dc_to_wc = vtkCoordinate()
        dc_to_wc.SetCoordinateSystemToDisplay()

        for i in range(point_count):
            point_position_dc = [0.0, 0.0, 0.0]
            points_display.GetPoint(i, point_position_dc)

            near, far = self._display_to_world(point_position_dc, dc_to_wc, view_node, renderer)

            points.SetPoint(2 * i, near[:3])
            points.SetPoint(2 * i + 1, far[:3])

            ids.SetId(0, 2 * i)
            ids.SetId(1, 2 * i + 1)
            ids.SetId(2, (2 * i + 3) % (2 * point_count))
            ids.SetId(3, (2 * i + 2) % (2 * point_count))
            cells.InsertNextCell(quad)

        return polydata

    @staticmethod
    def _is_slice_view(view_node: vtkMRMLAbstractViewNode):
        return isinstance(view_node, vtkMRMLSliceNode)

    def _display_to_world(
        self,
        display_coords: list[float],
        dc_to_wc: vtkCoordinate,
        view_node: vtkMRMLAbstractViewNode,
        renderer: vtkRenderer,
    ) -> tuple[list[float], list[float]]:
        if self._is_slice_view(view_node):
            return self._display_to_world_slice(display_coords, view_node)
        return self._display_to_world_generic(display_coords, dc_to_wc, renderer)

    def _display_to_world_slice(
        self, display_coords: list[float], slice_node: vtkMRMLSliceNode
    ) -> tuple[list[float], list[float]]:
        xy_to_slice: vtkMatrix4x4 = slice_node.GetXYToRAS()

        max_dim = max(self._modifier.volume_node.GetImageData().GetBounds())

        # Default: ScissorsSegmentationSliceCut.UNLIMITED
        near = xy_to_slice.MultiplyPoint([display_coords[0], display_coords[1], -max_dim, 1.0])
        far = xy_to_slice.MultiplyPoint([display_coords[0], display_coords[1], max_dim, 1.0])
        return list(near), list(far)

    @classmethod
    def _display_to_world_generic(
        cls, display_coords: list[float], dc_to_wc: vtkCoordinate, renderer: vtkRenderer
    ) -> tuple[list[float], list[float]]:
        dc_to_wc.SetValue(display_coords[0], display_coords[1], 0.0)
        near = dc_to_wc.GetComputedWorldValue(renderer)

        dc_to_wc.SetValue(display_coords[0], display_coords[1], 1.0)
        far = dc_to_wc.GetComputedWorldValue(renderer)

        return list(near), list(far)

    def _polydata_to_stencil(self, polydata: vtkPolyData) -> vtkImageStencilData:
        triangulator = vtkTriangleFilter()
        triangulator.SetInputData(polydata)
        triangulator.Update()

        converter = vtkPolyDataToImageStencil()
        reference = self.modifier.create_modifier_labelmap()
        identity = vtkMatrix4x4()
        identity.Identity()
        reference.SetGeometryFromImageToWorldMatrix(identity)

        converter.SetInputConnection(triangulator.GetOutputPort())
        converter.SetInformationInput(reference)
        converter.Update()

        return converter.GetOutput()

    def _polydata_to_oriented_image(self, polydata):
        reference = self.modifier.create_modifier_labelmap()

        mat = vtkMatrix4x4()
        reference.GetImageToWorldMatrix(mat)
        mat.Invert()
        transform = vtkTransform()
        transform.SetMatrix(mat)
        transform_filter = vtkTransformFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputData(polydata)
        transform_filter.Update()

        stencil = self._polydata_to_stencil(transform_filter.GetOutput())
        stencil_to_image = vtkImageStencilToImage()
        stencil_to_image.SetInputData(stencil)
        stencil_to_image.SetInsideValue(1)
        stencil_to_image.Update()
        image = stencil_to_image.GetOutput()
        oriented_image = vtkOrientedImageData()
        oriented_image.DeepCopy(image)
        oriented_image.CopyDirections(reference)
        oriented_image.SetOrigin(reference.GetOrigin())
        mat = vtkMatrix4x4()
        self.modifier.create_modifier_labelmap().GetImageToWorldMatrix(mat)
        oriented_image.SetGeometryFromImageToWorldMatrix(mat)

        return oriented_image

    def apply_points_display_coordinates(self, points_display: vtkPoints, view: AbstractView) -> None:
        """
        Apply scissors points as defined in display coordinates in the input view.
        """

        stencil_polydata = self._stencil_polydata_from_display_coordinates(points_display, view)
        stencil_image_data = self._polydata_to_oriented_image(stencil_polydata)
        stencil_array = vtk_image_to_np(stencil_image_data)
        segment_array = vtk_image_to_np(self.modifier.get_segment_labelmap(self.modifier.active_segment_id))
        if segment_array.shape == (0, 0, 0):
            segment_array = np.zeros_like(stencil_array)
        mask_array = self._create_bounding_mask(segment_array, view.get_view_node())

        match self._fill_mode:
            case ScissorsEffectFillMode.ERASE_OUTSIDE:
                self._erase_outside(segment_array, stencil_array, mask_array)
            case ScissorsEffectFillMode.FILL_OUTSIDE:
                self._fill_outside(segment_array, stencil_array, mask_array)
            case ScissorsEffectFillMode.ERASE_INSIDE:
                self._erase_inside(segment_array, stencil_array, mask_array)
            case ScissorsEffectFillMode.FILL_INSIDE:
                self._fill_inside(segment_array, stencil_array, mask_array)

        self.modifier.set_segment_labelmap(self.modifier.active_segment_id, segment_array)

    def _fill_inside(self, segment_array: NDArray, stencil_array: NDArray, mask_array: NDArray) -> None:
        self.set_mode(ModificationMode.Add)
        segment_array[np.where(np.logical_and(mask_array, stencil_array != 0))] = 1

    def _erase_inside(self, segment_array: NDArray, stencil_array: NDArray, mask_array: NDArray) -> None:
        self.set_mode(ModificationMode.Remove)
        segment_array[np.where(np.logical_and(mask_array, stencil_array != 0))] = 0

    def _fill_outside(self, segment_array: NDArray, stencil_array: NDArray, mask_array: NDArray) -> None:
        self.set_mode(ModificationMode.Add)
        if self._range_mode == ScissorsEffectRangeMode.SYMMETRIC:
            # Special case to replicate 3D Slicer behavior
            # Fill segment outside of mask region
            segment_array[np.where(mask_array == 0)] = 1
        segment_array[np.where(np.logical_and(mask_array, stencil_array == 0))] = 1

    def _erase_outside(self, segment_array: NDArray, stencil_array: NDArray, mask_array: NDArray) -> None:
        self.set_mode(ModificationMode.Add)
        segment_array[np.where(np.logical_and(mask_array, stencil_array == 0))] = 0
        if self._range_mode == ScissorsEffectRangeMode.SYMMETRIC:
            # Special case to replicate 3D Slicer behavior
            # Erase segment outside of mask region
            segment_array[np.where(mask_array == 0)] = 0

    def _create_bounding_mask(self, segment_array: NDArray, view_node: AbstractView) -> NDArray:
        """Define bounding mask based on SliceCut mode (ignored in 3D)"""
        if not self._is_slice_view(view_node):
            return np.ones_like(segment_array)

        modifier_labelmap = self.modifier.create_modifier_labelmap()
        segmentation_to_world = vtkMatrix4x4()
        vtkMRMLTransformNode.GetMatrixTransformBetweenNodes(
            self.modifier.segmentation.segmentation_node.GetParentTransformNode(), None, segmentation_to_world
        )
        segmentation_to_XY = vtkTransform()
        worldToSliceXYMatrix = vtkMatrix4x4()
        vtkMatrix4x4.Invert(view_node.GetXYToRAS(), worldToSliceXYMatrix)
        segmentation_to_XY.Concatenate(worldToSliceXYMatrix)
        segmentation_to_XY.Concatenate(segmentation_to_world)
        segmentation_XY_bounds = [0, -1, 0, -1, 0, -1]
        original_segmentation_XY_bounds = [0, -1, 0, -1, 0, -1]
        vtkOrientedImageDataResample.TransformOrientedImageDataBounds(
            modifier_labelmap, segmentation_to_XY, segmentation_XY_bounds
        )
        vtkOrientedImageDataResample.TransformOrientedImageDataBounds(
            modifier_labelmap, segmentation_to_XY, original_segmentation_XY_bounds
        )

        mat = view_node.GetXYToRAS()
        cube = vtkCubeSource()
        bounds = segmentation_XY_bounds
        if self._range_mode == ScissorsEffectRangeMode.POSITIVE:
            bounds[4] = -0.5
            bounds[5] = original_segmentation_XY_bounds[5]
        elif self._range_mode == ScissorsEffectRangeMode.NEGATIVE:
            bounds[4] = original_segmentation_XY_bounds[4]
            bounds[5] = 0.5
        elif self._range_mode == ScissorsEffectRangeMode.SYMMETRIC:
            vector = [0, 0, 1, 0]
            world_vector = mat.MultiplyPoint(vector)
            norm = np.linalg.norm(world_vector)
            distance = max(0.5, self._symmetric_distance / norm / 2)
            bounds[4] = -distance
            bounds[5] = distance

        cube.SetBounds(bounds)
        transform = vtkTransform()
        transform_filter = vtkTransformFilter()
        transform_filter.SetTransform(transform)
        transform.SetMatrix(mat)
        transform_filter.SetInputConnection(cube.GetOutputPort())
        transform_filter.Update()
        mask = self._polydata_to_oriented_image(transform_filter.GetOutput())
        return vtk_image_to_np(mask)
