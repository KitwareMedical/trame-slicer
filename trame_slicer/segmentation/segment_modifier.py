from __future__ import annotations

import enum
import logging
import math
from collections.abc import Generator
from dataclasses import dataclass
from enum import auto

from numpy.typing import NDArray
from slicer import (
    vtkMRMLSegmentationNode,
    vtkMRMLSegmentEditorNode,
    vtkMRMLTransformNode,
    vtkOrientedImageData,
    vtkOrientedImageDataResample,
    vtkSlicerSegmentEditorLogic,
)
from undo_stack import Signal
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_CHAR, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPolyData
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkFiltersModeling import vtkFillHolesFilter
from vtkmodules.vtkImagingCore import vtkImageChangeInformation
from vtkmodules.vtkImagingStencil import (
    vtkImageStencilToImage,
    vtkPolyDataToImageStencil,
)

from .segmentation import Segmentation
from .segmentation_undo_command import SegmentationLabelMapUndoCommand


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
    Set = auto()
    Add = auto()
    Remove = auto()
    RemoveAll = auto()


class SegmentationEditableArea(enum.Enum):
    EVERYWHERE = "EditAllowedEverywhere"
    INSIDE_ALL_SEGMENTS = "EditAllowedInsideAllSegments"
    INSIDE_ALL_VISIBLE_SEGMENTS = "EditAllowedInsideVisibleSegments"
    OUTSIDE_ALL_SEGMENTS = "EditAllowedOutsideAllSegments"
    OUTSIDE_ALL_VISIBLE_SEGMENTS = "EditAllowedOutsideVisibleSegments"


class SegmentOverwriteMode(enum.Enum):
    OVERWRITE_ALL = vtkMRMLSegmentEditorNode.OverwriteAllSegments
    OVERWRITE_ALL_VISIBLE_SEGMENTS = vtkMRMLSegmentEditorNode.OverwriteVisibleSegments
    ALLOW_OVERLAP = vtkMRMLSegmentEditorNode.OverwriteNone


@dataclass
class SegmentModificationParameters:
    editable_area: SegmentationEditableArea | None = SegmentationEditableArea.EVERYWHERE
    segment_id: str | None = None
    overwrite_mode: SegmentOverwriteMode = SegmentOverwriteMode.OVERWRITE_ALL


class SegmentModifier:
    """
    Helper class to apply modifications to a given segment in the segmentation of a segmentation node.
    Should be used by segmentation widgets.
    """

    segmentation_modified = Signal()
    segment_editor_node_modified = Signal()

    def __init__(self, segmentation: Segmentation) -> None:
        self._segmentation: Segmentation = segmentation
        self.logic.AddObserver(vtkMRMLSegmentEditorNode.EffectParameterModified, self.segment_editor_node_modified)
        self._active_segment_id = self._segmentation.get_nth_segment_id(0)

        self._modification_mode = ModificationMode.Add
        self._segmentation.segmentation_modified.connect(self.segmentation_modified)
        self._segmentation.segmentation_modified.connect(self.on_segmentation_modified)

    @property
    def logic(self) -> vtkSlicerSegmentEditorLogic:
        return self._segmentation.editor_logic

    @property
    def segment_editor_node(self) -> vtkMRMLSegmentEditorNode | None:
        if not self.logic:
            return None
        return self.logic.GetSegmentEditorNode()

    @property
    def active_segment_id(self):
        return self._active_segment_id

    @active_segment_id.setter
    def active_segment_id(self, segment_id):
        if segment_id not in self._segmentation.get_segment_ids():
            segment_id = ""
        self._active_segment_id = segment_id

    @property
    def modification_mode(self) -> ModificationMode:
        return self._modification_mode

    @modification_mode.setter
    def modification_mode(self, mode: ModificationMode) -> None:
        self._modification_mode = mode

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
        brush_labelmap = self._poly_to_image_data(brush_model)
        modifier_labelmap = self.segmentation.create_modifier_labelmap()

        points_ijk = self._world_points_to_ijk(world_locations)
        brush_positioner = vtkImageChangeInformation()
        brush_positioner.SetInputData(brush_labelmap)
        brush_positioner.SetOutputSpacing(modifier_labelmap.GetSpacing())
        brush_positioner.SetOutputOrigin(modifier_labelmap.GetOrigin())

        modifier_extent = [0, -1, 0, -1, 0, -1]
        oriented_brush_positioner_output = vtkOrientedImageData()
        for i in range(points_ijk.GetNumberOfPoints()):
            brush_positioner.SetExtentTranslation([int(p) for p in points_ijk.GetPoint(i)])
            brush_positioner.Update()

            oriented_brush_positioner_output.ShallowCopy(brush_positioner.GetOutput())
            oriented_brush_positioner_output.CopyDirections(modifier_labelmap)
            if i == 0:
                modifier_extent = list(oriented_brush_positioner_output.GetExtent())
            else:
                brush_extent = oriented_brush_positioner_output.GetExtent()
                for i_extent in range(3):
                    modifier_extent[i_extent * 2] = min(modifier_extent[i_extent * 2], brush_extent[i_extent * 2])
                    modifier_extent[i_extent * 2 + 1] = max(
                        modifier_extent[i_extent * 2 + 1], brush_extent[i_extent * 2 + 1]
                    )

            vtkOrientedImageDataResample.ModifyImage(
                modifier_labelmap, oriented_brush_positioner_output, vtkOrientedImageDataResample.OPERATION_MAXIMUM
            )

        self.apply_labelmap(modifier_labelmap, modifier_extent=modifier_extent)
        self.trigger_active_segment_modified()

    def apply_polydata_world(self, poly_world: vtkPolyData):
        """
        :param poly_world: Poly in world coordinates
        """
        if self.active_segment_id == "":
            return

        poly_ijk = self._world_poly_to_ijk(poly_world)
        poly_modifier = self._poly_to_image_data(poly_ijk)
        modifier_labelmap = self._poly_image_data_to_modifier_labelmap(poly_modifier)
        self.apply_labelmap(modifier_labelmap)

    def _poly_image_data_to_modifier_labelmap(self, poly_modifier: vtkOrientedImageData) -> vtkOrientedImageData | None:
        modifier_labelmap = self.segmentation.create_modifier_labelmap()
        brush_positioner = vtkImageChangeInformation()
        brush_positioner.SetInputData(poly_modifier)
        brush_positioner.SetOutputSpacing(modifier_labelmap.GetSpacing())
        brush_positioner.SetOutputOrigin(modifier_labelmap.GetOrigin())
        brush_positioner.Update()

        oriented_labelmap = vtkOrientedImageData()
        oriented_labelmap.ShallowCopy(brush_positioner.GetOutput())
        oriented_labelmap.CopyDirections(modifier_labelmap)
        vtkOrientedImageDataResample.ModifyImage(
            modifier_labelmap, oriented_labelmap, vtkOrientedImageDataResample.OPERATION_MAXIMUM
        )
        return modifier_labelmap

    def apply_labelmap(
        self,
        modifier_labelmap: vtkImageData,
        *,
        modifier_extent=None,
        is_per_segment: bool = True,
        do_bypass_masking: bool = False,
    ):
        """
        Modify active segment using input modifier labelmap in source IJK coordinates.
        When applying, pushes the modifications to the current undo stack if any is defined.
        """
        with SegmentationLabelMapUndoCommand.push_state_change(self.segmentation):
            self._modify_active_segment_by_labelmap(
                modifier_labelmap,
                modifier_extent=modifier_extent,
                is_per_segment=is_per_segment,
                do_bypass_masking=do_bypass_masking,
            )
        self.trigger_active_segment_modified()

    def _modify_active_segment_by_labelmap(
        self,
        modifier_labelmap: vtkImageData,
        *,
        modifier_extent=None,
        is_per_segment: bool = True,
        do_bypass_masking: bool = False,
    ):
        if not self.logic or self.active_segment_id == "":
            return

        if modifier_extent is None:
            modifier_extent = [0, -1, 0, -1, 0, -1]

        modifier_mode = {
            ModificationMode.Set: vtkSlicerSegmentEditorLogic.ModificationModeSet,
            ModificationMode.Add: vtkSlicerSegmentEditorLogic.ModificationModeAdd,
            ModificationMode.Remove: vtkSlicerSegmentEditorLogic.ModificationModeRemove,
            ModificationMode.RemoveAll: vtkSlicerSegmentEditorLogic.ModificationModeRemoveAll,
        }[self.modification_mode]

        self.logic.ModifySegmentByLabelmap(
            self.segmentation.segmentation_node,
            self.active_segment_id,
            modifier_labelmap,
            modifier_mode,
            modifier_extent,
            is_per_segment,
            do_bypass_masking,
        )

    def get_segment_labelmap(self, segment_id, *, as_numpy_array=False) -> NDArray | vtkImageData:
        return self._segmentation.get_segment_labelmap(segment_id=segment_id, as_numpy_array=as_numpy_array)

    @staticmethod
    def _poly_to_image_data(poly: vtkPolyData) -> vtkOrientedImageData:
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

    def get_source_image_data(self) -> vtkOrientedImageData | None:
        if not self.logic:
            return None
        self.logic.UpdateAlignedSourceVolume()
        return self.logic.GetAlignedSourceVolume()

    def create_modifier_labelmap(self) -> vtkOrientedImageData | None:
        if not self.segmentation:
            return None
        return self.segmentation.create_modifier_labelmap()

    def set_source_volume_intensity_mask_range(self, min_value: float, max_value: float) -> None:
        if not self.segment_editor_node:
            return

        self.segment_editor_node.SetSourceVolumeIntensityMaskRange(min_value, max_value)

    def get_source_volume_intensity_mask_range(self) -> tuple[float, float] | None:
        if not self.segment_editor_node:
            return None
        return self.segment_editor_node.GetSourceVolumeIntensityMaskRange()

    def set_source_volume_intensity_mask_enabled(self, is_enabled: bool) -> None:
        if not self.segment_editor_node:
            return

        self.segment_editor_node.SetSourceVolumeIntensityMask(is_enabled)

    def is_source_volume_intensity_mask_enabled(self) -> bool:
        if not self.segment_editor_node:
            return False
        return self.segment_editor_node.GetSourceVolumeIntensityMask()

    def set_segment_modification_parameters(self, parameters: SegmentModificationParameters) -> None:
        if parameters.segment_id is None:
            self._set_editable_area(parameters.editable_area)
        else:
            self._set_editable_area_to_segment(parameters.segment_id)
        self._set_overwrite_mode(parameters.overwrite_mode)

    def get_segment_modification_parameters(
        self,
    ) -> SegmentModificationParameters | None:
        if self.segment_editor_node is None:
            return None
        editable_area = self._get_editable_area()
        editable_segment_id = self._get_editable_segment_id()
        return SegmentModificationParameters(
            editable_area=editable_area,
            segment_id=editable_segment_id if editable_area is None else None,
            overwrite_mode=self._get_overwrite_mode(),
        )

    def _set_editable_area(self, editable_area: SegmentationEditableArea) -> None:
        if self.segment_editor_node is None or editable_area not in SegmentationEditableArea:
            return
        mask_mode = self.segmentation.segmentation_node.ConvertMaskModeFromString(editable_area.value)
        self.segment_editor_node.SetMaskMode(mask_mode)

    def _get_editable_area(self) -> SegmentationEditableArea | None:
        if self.segment_editor_node is None:
            return None
        mask_mode = self.segment_editor_node.GetMaskMode()
        mask_mode_string = self.segmentation.segmentation_node.ConvertMaskModeToString(mask_mode)
        if mask_mode_string == "EditAllowedInsideSingleSegment":
            # String associated with vtkMRMLSegmentationNode::EditAllowedInsideSingleSegment
            # i.e. Inside Segment X, which is not exposed through SegmentationEditableArea
            return None
        return SegmentationEditableArea(mask_mode_string)

    def _set_editable_area_to_segment(self, segment_id: str) -> None:
        if self.segment_editor_node is None or segment_id not in self.segmentation.get_segment_ids():
            return
        self.segment_editor_node.SetMaskSegmentID(segment_id)
        self.segment_editor_node.SetMaskMode(vtkMRMLSegmentationNode.EditAllowedInsideSingleSegment)

    def _get_editable_segment_id(self) -> str | None:
        if self.segment_editor_node is None:
            return None
        return self.segment_editor_node.GetMaskSegmentID()

    def _set_overwrite_mode(self, overwrite_mode: SegmentOverwriteMode) -> None:
        if self.segment_editor_node is None:
            return
        self.segment_editor_node.SetOverwriteMode(overwrite_mode)

    def _get_overwrite_mode(self) -> SegmentOverwriteMode | None:
        if self.segment_editor_node is None:
            return None
        overwrite_mode = self.segment_editor_node.GetOverwriteMode()
        return SegmentOverwriteMode(overwrite_mode)

    def group_undo_commands(self, text: str = "") -> Generator:
        return self.segmentation.group_undo_commands(text)
