from __future__ import annotations

from enum import Enum, auto

import numpy as np
from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLNode,
    vtkMRMLSliceNode,
    vtkOrientedImageData,
    vtkSlicerSegmentationsModuleLogic,
)
from vtkmodules.vtkCommonCore import vtkIntArray
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkImagingCore import vtkImageCast, vtkImageThreshold

from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_undo_command import SegmentationLabelMapUndoCommand

try:
    from slicer import vtkITKIslandMath
except ImportError:
    from vtkITK import vtkITKIslandMath


class SegmentationIslandsMode(Enum):
    KEEP_LARGEST_ISLAND = auto()
    REMOVE_SMALL_ISLANDS = auto()
    SPLIT_TO_SEGMENTS = auto()
    KEEP_SELECTED = auto()
    REMOVE_SELECTED = auto()
    ADD_SELECTED = auto()

    @classmethod
    def get_interactive_modes(cls) -> list[SegmentationIslandsMode]:
        return [
            SegmentationIslandsMode.KEEP_SELECTED,
            SegmentationIslandsMode.REMOVE_SELECTED,
            SegmentationIslandsMode.ADD_SELECTED,
        ]

    def is_interactive(self) -> bool:
        return self in self.get_interactive_modes()


class SegmentationEffectIslands(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()
        self.set_mode(ModificationMode.Set)

        self._island_mode: SegmentationIslandsMode = SegmentationIslandsMode.KEEP_LARGEST_ISLAND
        self._minimum_island_size: int = 0

    def _create_pipeline(self, view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode) -> None:
        from .segmentation_islands_pipeline import SegmentationIslandsPipeline

        if isinstance(view_node, vtkMRMLSliceNode):
            return SegmentationIslandsPipeline()
        return None

    def is_in_interactive_mode(self) -> bool:
        return self._island_mode.is_interactive()

    def set_island_mode(self, island_mode: SegmentationIslandsMode) -> None:
        if self._island_mode == island_mode:
            return
        self._island_mode = island_mode
        self.parameters_changed.emit()

    def get_island_mode(self) -> SegmentationIslandsMode:
        return self._island_mode

    def set_minimum_island_size(self, minimum_island_size: int) -> None:
        if self._minimum_island_size == minimum_island_size:
            return
        self._minimum_island_size = minimum_island_size
        self.parameters_changed.emit()

    def get_minimum_island_size(self) -> int:
        return self._minimum_island_size

    def apply(self, island_mode: SegmentationIslandsMode | None = None) -> None:
        island_mode = island_mode or self._island_mode

        if island_mode.is_interactive():
            return

        match island_mode:
            case SegmentationIslandsMode.KEEP_LARGEST_ISLAND:
                self.keep_largest_island()
            case SegmentationIslandsMode.REMOVE_SMALL_ISLANDS:
                self.remove_small_islands()
            case SegmentationIslandsMode.SPLIT_TO_SEGMENTS:
                self.split_islands_to_segments()

    def select_island_at_position(
        self,
        world_pos: tuple[float, float, float],
        island_mode: SegmentationIslandsMode | None = None,
    ) -> None:
        island_mode = island_mode or self._island_mode

        if not island_mode.is_interactive():
            return

        match island_mode:
            case SegmentationIslandsMode.KEEP_SELECTED:
                self.keep_island_at_position(world_pos)
            case SegmentationIslandsMode.REMOVE_SELECTED:
                self.remove_island_at_position(world_pos)
            case SegmentationIslandsMode.ADD_SELECTED:
                self.add_island_at_position(world_pos)

    def _get_label_values(self, segment_id: str | None = None) -> list[float]:
        island_image = self.get_island_labelmap(segment_id=segment_id)
        label_values_array = vtkIntArray()
        vtkSlicerSegmentationsModuleLogic.GetAllLabelValues(label_values_array, island_image)

        return [int(label_values_array.GetTuple1(i)) for i in range(label_values_array.GetNumberOfTuples())]

    def _get_label_value_at_position(
        self, world_pos: tuple[float, float, float], segment_id: str | None = None
    ) -> float:
        island_image = self.get_island_labelmap(segment_id=segment_id)
        world_to_image_mat = vtkMatrix4x4()
        island_image.GetWorldToImageMatrix(world_to_image_mat)
        image_pos = world_to_image_mat.MultiplyPoint([*world_pos, 1.0])
        return island_image.GetScalarComponentAsFloat(*[int(np.round(pos)) for pos in image_pos[:3]], 0)

    def _remove_islands_by_labels(self, labels_to_remove: list[float]):
        if not labels_to_remove:
            return

        island_image = self.get_island_labelmap()
        modifier_image = self.modifier.create_modifier_labelmap()

        threshold = vtkImageThreshold()
        threshold.SetInputData(island_image)
        threshold.ReplaceOutOff()

        for label_value in self._get_label_values():
            if label_value in labels_to_remove:
                threshold.ThresholdBetween(label_value, label_value)
                threshold.SetInValue(0)
                threshold.Update()
                threshold.SetInputData(threshold.GetOutput())

        modifier_image.DeepCopy(threshold.GetOutput())
        self.modifier.apply_labelmap(modifier_image)

    def remove_island_at_position(self, world_pos: tuple[float, float, float]):
        if not self.is_active:
            return

        label_value = self._get_label_value_at_position(world_pos)
        if label_value == 0:
            return

        self._remove_islands_by_labels([label_value])

    def keep_island_at_position(self, world_pos: tuple[float, float, float]):
        if not self.is_active:
            return

        label_value = self._get_label_value_at_position(world_pos)
        if label_value == 0:
            return

        self._remove_islands_by_labels([label for label in self._get_label_values() if label != label_value])

    def add_island_at_position(self, world_pos: tuple[float, float, float]):
        if not self.is_active:
            return

        # The modifier needs to be in Add mode temporarily
        modification_mode = self.modifier.modification_mode
        self.modifier.modification_mode = ModificationMode.Add

        try:
            # Search for another segment with an island at these coordinates
            for other_segment_id in self.modifier.segmentation.get_segment_ids()[::-1]:
                if other_segment_id == self.modifier.active_segment_id:
                    continue

                label_value = self._get_label_value_at_position(world_pos, other_segment_id)
                if label_value == 0:
                    continue

                # Add island to active segment
                modifier_image = self.modifier.create_modifier_labelmap()
                threshold = vtkImageThreshold()
                threshold.SetInputData(self.get_island_labelmap(segment_id=other_segment_id))
                threshold.ThresholdBetween(label_value, label_value)
                threshold.SetInValue(label_value)
                threshold.SetOutValue(0)
                threshold.Update()
                modifier_image.DeepCopy(threshold.GetOutput())
                self.modifier.apply_labelmap(modifier_image)
                return

        finally:
            # Ensure modifier's initial modification mode is reapplied
            self.modifier.modification_mode = modification_mode

    def remove_small_islands(self, min_voxel_size: int | None = None) -> None:
        if not self.is_active:
            return

        island_image = self.get_island_labelmap(min_voxel_size=min_voxel_size or self._minimum_island_size)
        self.modifier.apply_labelmap(island_image)

    def keep_n_largest_islands(self, number_of_islands: int) -> None:
        if not self.is_active:
            return

        modifier_image = self.modifier.create_modifier_labelmap()
        if number_of_islands <= 0:
            self.modifier.apply_labelmap(modifier_image)
            return

        # Labels are ordered by size
        label_values = self._get_label_values()
        if number_of_islands > len(label_values):
            return

        self._remove_islands_by_labels(label_values[number_of_islands:])

    def keep_largest_island(self) -> None:
        self.keep_n_largest_islands(1)

    def split_islands_to_segments(self) -> None:
        if not self.is_active:
            return

        island_image = self.get_island_labelmap()
        label_values = self._get_label_values()

        if len(label_values) <= 1:
            return

        modifier_image = self.modifier.create_modifier_labelmap()

        threshold = vtkImageThreshold()
        threshold.SetInputData(island_image)

        # Replace selected segment's labelmap by first island
        initial_label_value = label_values[0]
        threshold.ThresholdBetween(initial_label_value, initial_label_value)
        threshold.SetInValue(initial_label_value)
        threshold.SetOutValue(0)
        threshold.Update()
        modifier_image.DeepCopy(threshold.GetOutput())

        # Create labelmap without first segment
        threshold.SetInValue(0)
        threshold.ReplaceOutOff()
        threshold.ThresholdBetween(initial_label_value, initial_label_value)
        threshold.Update()

        with self.modifier.group_undo_commands(f"{__class__} - Split {self.modifier.active_segment_id}"):
            self.modifier.apply_labelmap(modifier_image)
            with SegmentationLabelMapUndoCommand.push_state_change(self.modifier.segmentation):
                modifier_image.DeepCopy(threshold.GetOutput())
                vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(
                    modifier_image,
                    self.modifier.segmentation.segmentation_node,
                    self.modifier.segmentation.get_segment(self.modifier.active_segment_id).GetName(),
                )
        self.modifier.segmentation.segmentation_modified.emit()

    def get_island_labelmap(self, *, min_voxel_size: int = 0, segment_id: str | None = None) -> vtkOrientedImageData:
        source_image_data = self.modifier.get_source_image_data()

        if segment_id is None:
            segment_id = self.modifier.active_segment_id
        segment_labelmap = self.modifier.get_segment_labelmap(segment_id)
        cast_in = vtkImageCast()
        cast_in.SetInputData(segment_labelmap)
        cast_in.SetOutputScalarTypeToUnsignedInt()

        island_math = vtkITKIslandMath()
        island_math.SetInputConnection(cast_in.GetOutputPort())
        island_math.SetFullyConnected(False)
        island_math.SetMinimumSize(min_voxel_size)
        island_math.Update()
        island_output = island_math.GetOutput()

        island_image = vtkOrientedImageData()
        island_image.ShallowCopy(island_output)
        image_to_world_matrix = vtkMatrix4x4()
        source_image_data.GetImageToWorldMatrix(image_to_world_matrix)
        island_image.SetImageToWorldMatrix(image_to_world_matrix)

        return island_image
