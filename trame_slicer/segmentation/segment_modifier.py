from __future__ import annotations

import enum
import logging
import math
from copy import deepcopy
from enum import auto

import numpy as np
from numpy.typing import NDArray
from slicer import vtkMRMLTransformNode
from undo_stack import Signal
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_CHAR, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPolyData
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkFiltersModeling import vtkFillHolesFilter
from vtkmodules.vtkImagingStencil import (
    vtkImageStencilToImage,
    vtkPolyDataToImageStencil,
)

from trame_slicer.utils import vtk_image_to_np

from .segment_region_mask import MaskedRegion, SegmentRegionMask
from .segmentation import Segmentation, SegmentationLabelMapUndoCommand


def _clamp_extent(extent: list[int], limits: list[int]) -> list[int]:
    return [
        max(extent[0], limits[0]),
        min(extent[1], limits[1]),
        max(extent[2], limits[2]),
        min(extent[3], limits[3]),
        max(extent[4], limits[4]),
        min(extent[5], limits[5]),
    ]


def _sub_extent_to_slices(extent: list[int], sub_extent: list[int]) -> tuple[slice, slice, slice]:
    """
    Convert a vtkImageData sub extent to NumPy slices
    """
    return (
        slice(
            sub_extent[4] - extent[4],
            sub_extent[4] - extent[4] + (sub_extent[5] - sub_extent[4] + 1),
        ),
        slice(
            sub_extent[2] - extent[2],
            sub_extent[2] - extent[2] + (sub_extent[3] - sub_extent[2] + 1),
        ),
        slice(
            sub_extent[0] - extent[0],
            sub_extent[0] - extent[0] + (sub_extent[1] - sub_extent[0] + 1),
        ),
    )


class ModificationMode(enum.IntEnum):
    # Paint
    Paint = auto()

    # Erase active segment
    Erase = auto()

    # Erase all segments
    EraseAll = auto()


class SegmentModifier:
    """
    Helper class to apply modifications to a given segment in the segmentation of a segmentation node.
    Should be used by segmentation widgets.
    """

    segmentation_modified = Signal()

    def __init__(self, segmentation: Segmentation) -> None:
        self._segmentation: Segmentation = segmentation
        self._active_segment_id = self._segmentation.get_nth_segment_id(0)

        self._modification_mode = ModificationMode.Paint
        self._region_mask = SegmentRegionMask(self._segmentation)
        self._mask = None
        self._segmentation.segmentation_modified.connect(self.segmentation_modified)
        self._segmentation.segmentation_modified.connect(self.on_segmentation_modified)

    @property
    def active_segment_id(self):
        return self._active_segment_id

    @active_segment_id.setter
    def active_segment_id(self, segment_id):
        if segment_id not in self._segmentation.get_segment_ids():
            segment_id = ""
        self._active_segment_id = segment_id

    @property
    def mask(self) -> NDArray[np.bool] | None:
        return self._mask

    @mask.setter
    def mask(self, val: NDArray[np.bool] | None):
        if val is not None and tuple(val.shape) != tuple(reversed(self.volume_node.GetImageData().GetDimensions())):
            _error_msg = "mask extent must match source volume extent"
            raise ValueError(_error_msg)

        self._mask = val

    @property
    def modification_mode(self) -> ModificationMode:
        return self._modification_mode

    @modification_mode.setter
    def modification_mode(self, mode: ModificationMode) -> None:
        self._modification_mode = mode

    @property
    def masked_region(self) -> MaskedRegion:
        return self._region_mask.masked_region

    @masked_region.setter
    def masked_region(self, region: MaskedRegion) -> None:
        self._region_mask.masked_region = region

    @property
    def selected_ids(self) -> list[str]:
        return self._region_mask.selected_ids

    @selected_ids.setter
    def selected_ids(self, selected_ids: list[str]):
        self._region_mask.selected_ids = selected_ids

    @property
    def segmentation(self) -> Segmentation:
        return self._segmentation

    @property
    def volume_node(self):
        return self._segmentation.volume_node

    def apply_glyph(self, poly: vtkPolyData, world_locations: vtkPoints) -> None:
        """
        :param poly: in world origin coordinates (no transform but world-coords sized)
        :param world_locations: each location where glyph will be rendered at (world-coords)
        """
        if self.active_segment_id == "":
            logging.warning("No active segment in apply_poly_glyph")
            return

        if world_locations.GetNumberOfPoints() == 0:
            logging.warning("No points in set polydata")
            return

        # Rotate poly to later be translated in ijk coordinates for each world_locations
        world_to_ijk_transform_matrix = vtkMatrix4x4()
        self.volume_node.GetIJKToRASMatrix(world_to_ijk_transform_matrix)
        world_to_ijk_transform_matrix.Invert()
        world_to_ijk_transform_matrix.SetElement(0, 3, 0)
        world_to_ijk_transform_matrix.SetElement(1, 3, 0)
        world_to_ijk_transform_matrix.SetElement(2, 3, 0)

        world_to_segmentation_transform_matrix = vtkMatrix4x4()
        world_to_segmentation_transform_matrix.Identity()
        vtkMRMLTransformNode.GetMatrixTransformBetweenNodes(
            None,
            self._segmentation.segmentation_node.GetParentTransformNode(),
            world_to_segmentation_transform_matrix,
        )
        world_to_segmentation_transform_matrix.SetElement(0, 3, 0)
        world_to_segmentation_transform_matrix.SetElement(1, 3, 0)
        world_to_segmentation_transform_matrix.SetElement(2, 3, 0)

        world_origin_to_modifier_labelmap_ijk_transform = vtkTransform()
        world_origin_to_modifier_labelmap_ijk_transform.Concatenate(world_to_ijk_transform_matrix)
        world_origin_to_modifier_labelmap_ijk_transform.Concatenate(world_to_segmentation_transform_matrix)

        world_origin_to_modifier_labelmap_ijk_transformer = vtkTransformPolyDataFilter()
        world_origin_to_modifier_labelmap_ijk_transformer.SetTransform(world_origin_to_modifier_labelmap_ijk_transform)
        world_origin_to_modifier_labelmap_ijk_transformer.SetInputData(poly)
        world_origin_to_modifier_labelmap_ijk_transformer.Update()

        # Pre-rotated polydata
        brush_model: vtkPolyData = world_origin_to_modifier_labelmap_ijk_transformer.GetOutput()

        modifier_labelmap = self._poly_to_modifier_labelmap(brush_model)
        original_extent = modifier_labelmap.GetExtent()
        np_modifier_labelmap = vtk_image_to_np(modifier_labelmap) > 0

        points_ijk = self._world_points_to_ijk(world_locations)

        with SegmentationLabelMapUndoCommand.push_state_change(self.segmentation):
            for i in range(points_ijk.GetNumberOfPoints()):
                position = points_ijk.GetPoint(i)
                # translate the modifier labelmap in IJK coords
                extent = [
                    original_extent[0] + int(position[0]),
                    original_extent[1] + int(position[0]),
                    original_extent[2] + int(position[1]),
                    original_extent[3] + int(position[1]),
                    original_extent[4] + int(position[2]),
                    original_extent[5] + int(position[2]),
                ]
                self._apply_binary_labelmap(np_modifier_labelmap, extent, do_trigger_segmentation_modified=False)

        self.trigger_active_segment_modified()

    def apply_polydata_world(self, poly_world: vtkPolyData):
        """
        :param poly_world: Poly in world coordinates
        """
        if self.active_segment_id == "":
            return

        poly_ijk = self._world_poly_to_ijk(poly_world)
        modifier_labelmap = self._poly_to_modifier_labelmap(poly_ijk)
        self.apply_labelmap(modifier_labelmap)

    def apply_labelmap(self, modifier_labelmap: vtkImageData):
        """
        :param modifier_labelmap: in source ijk coordinates, VTK image data version
        """

        with SegmentationLabelMapUndoCommand.push_state_change(self.segmentation):
            np_modifier_labelmap = vtk_image_to_np(modifier_labelmap) > 0
            self._apply_binary_labelmap(np_modifier_labelmap, list(modifier_labelmap.GetExtent()))

    def get_segment_labelmap(self, segment_id, *, as_numpy_array=False) -> NDArray | vtkImageData:
        return self._segmentation.get_segment_labelmap(segment_id=segment_id, as_numpy_array=as_numpy_array)

    def _apply_binary_labelmap(
        self,
        modifier_labelmap: NDArray[np.bool],
        base_modifier_extent: list[int],
        do_trigger_segmentation_modified=True,
    ):
        """
        :param modifier_labelmap: in source ijk coordinates
        :param base_modifier_extent: Extent of the modifier
        :param do_trigger_segmentation_modified: When True updates the surface representation if active.
        """
        if self.active_segment_id == "":
            return

        segment = self._segmentation.get_segment(self.active_segment_id)
        labelmap: vtkImageData = self.get_segment_labelmap(self.active_segment_id)

        common_extent = list(labelmap.GetExtent())
        # clamp modifier extent to common extent so we don't draw outside the segmentation!
        modifier_extent = _clamp_extent(base_modifier_extent, common_extent)

        np_labelmap = vtk_image_to_np(labelmap)
        labelmap_slices = _sub_extent_to_slices(common_extent, modifier_extent)
        modifier_labelmap_slices = _sub_extent_to_slices(base_modifier_extent, modifier_extent)

        if any(s.stop - s.start <= 0 for s in labelmap_slices) or any(
            s.stop - s.start <= 0 for s in modifier_labelmap_slices
        ):
            # nothing to do, affected labelmap area is empty or out of labelmap range
            return

        label_value = segment.GetLabelValue() if self.modification_mode == ModificationMode.Paint else 0
        active_label_value = segment.GetLabelValue()

        # Apply effect
        self._apply_modifier_labelmap_to_labelmap(
            labelmap=np_labelmap[labelmap_slices],
            modifier=modifier_labelmap[modifier_labelmap_slices],
            mask=self._mask[labelmap_slices] if self._mask is not None else None,
            label_value=label_value,
            active_label_value=active_label_value,
        )

        labelmap.GetPointData().GetScalars().Modified()
        if do_trigger_segmentation_modified:
            self.trigger_active_segment_modified()

    def _apply_modifier_labelmap_to_labelmap(
        self,
        *,
        labelmap: np.ndarray,
        modifier: NDArray[np.bool],
        mask: NDArray[np.bool] | None,
        label_value: int,
        active_label_value: int,
    ) -> None:
        # Copy input modifier since we will apply mutating op on it with masking.
        modifier = deepcopy(modifier)
        if mask is not None:
            modifier &= mask

        if self.modification_mode == ModificationMode.Erase:
            modifier &= labelmap == active_label_value

        modifier &= self._region_mask.get_masked_region(labelmap)
        labelmap[modifier] = label_value

    @staticmethod
    def _poly_to_modifier_labelmap(poly: vtkPolyData) -> vtkImageData:
        filler = vtkFillHolesFilter()
        filler.SetInputData(poly)
        filler.SetHoleSize(4096.0)
        filler.Update()
        filled_poly = filler.GetOutput()

        bounds = filled_poly.GetBounds()
        extent = [
            math.floor(bounds[0]) - 1,
            math.ceil(bounds[1]) + 1,
            math.floor(bounds[2]) - 1,
            math.ceil(bounds[3]) + 1,
            math.floor(bounds[4]) - 1,
            math.ceil(bounds[5]) + 1,
        ]
        brush_poly_data_to_stencil = vtkPolyDataToImageStencil()
        brush_poly_data_to_stencil.SetInputData(filled_poly)
        brush_poly_data_to_stencil.SetOutputSpacing(1.0, 1.0, 1.0)
        brush_poly_data_to_stencil.SetOutputWholeExtent(extent)

        stencilToImage = vtkImageStencilToImage()
        stencilToImage.SetInputConnection(brush_poly_data_to_stencil.GetOutputPort())
        stencilToImage.SetInsideValue(1.0)
        stencilToImage.SetOutsideValue(0.0)
        stencilToImage.SetOutputScalarType(VTK_UNSIGNED_CHAR)
        stencilToImage.Update()

        return stencilToImage.GetOutput()

    def _world_points_to_ijk(self, points: vtkPoints) -> vtkPoints:
        world_to_ijk_transform_matrix = vtkMatrix4x4()
        self.volume_node.GetIJKToRASMatrix(world_to_ijk_transform_matrix)
        world_to_ijk_transform_matrix.Invert()

        world_to_ijk_transform = vtkTransform()
        world_to_ijk_transform.Identity()
        world_to_ijk_transform.Concatenate(world_to_ijk_transform_matrix)

        ijk_points = vtkPoints()
        world_to_ijk_transform.TransformPoints(points, ijk_points)

        return ijk_points

    def _world_poly_to_ijk(self, poly: vtkPolyData) -> vtkPolyData:
        world_to_ijk_transform_matrix = vtkMatrix4x4()
        self.volume_node.GetIJKToRASMatrix(world_to_ijk_transform_matrix)
        world_to_ijk_transform_matrix.Invert()

        world_to_ijk_transform = vtkTransform()
        world_to_ijk_transform.Identity()
        world_to_ijk_transform.Concatenate(world_to_ijk_transform_matrix)

        poly_transformer = vtkTransformPolyDataFilter()
        poly_transformer.SetInputData(poly)
        poly_transformer.SetTransform(world_to_ijk_transform)
        poly_transformer.Update()

        return poly_transformer.GetOutput()

    def trigger_active_segment_modified(self):
        self.segmentation.trigger_modified()

    def on_segmentation_modified(self):
        if self.active_segment_id not in self._segmentation.get_segment_ids():
            self.active_segment_id = ""
