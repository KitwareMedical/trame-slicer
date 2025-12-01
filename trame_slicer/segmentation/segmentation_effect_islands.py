from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLNode,
    vtkOrientedImageData,
    vtkSlicerSegmentationsModuleLogic,
)
from vtkmodules.vtkCommonCore import vtkIntArray
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkImagingCore import vtkImageCast, vtkImageThreshold

try:
    from vtkmodules.vtkITK import vtkITKIslandMath
except ImportError:
    from vtkITK import vtkITKIslandMath

from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_undo_command import SegmentationLabelMapUndoCommand


class SegmentationEffectIslands(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()
        self.set_mode(ModificationMode.Set)

    def _create_pipeline(self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode) -> None:
        # Islands effect does not require a pipeline
        return None

    def remove_small_islands(self, min_voxel_size: int) -> None:
        if not self.is_active:
            return

        island_image = self.get_island_labelmap(min_voxel_size)
        self.modifier.apply_labelmap(island_image)

    def keep_n_largest_islands(self, number_of_islands: int) -> None:
        if not self.is_active:
            return

        modifier_image = self.modifier.create_modifier_labelmap()
        if number_of_islands <= 0:
            self.modifier.apply_labelmap(modifier_image)
            return

        island_image = self.get_island_labelmap()
        label_values = vtkIntArray()
        vtkSlicerSegmentationsModuleLogic.GetAllLabelValues(label_values, island_image)
        max_label_value = label_values.GetNumberOfTuples()
        if number_of_islands >= max_label_value:
            return

        modifier_image = self.modifier.create_modifier_labelmap()
        threshold = vtkImageThreshold()
        threshold.SetInputData(island_image)
        threshold.ReplaceOutOff()

        for i in range(number_of_islands, max_label_value):
            label_value = int(label_values.GetTuple1(i))
            threshold.ThresholdBetween(label_value, label_value)
            threshold.SetInValue(0)
            threshold.Update()
            threshold.SetInputData(threshold.GetOutput())

        modifier_image.DeepCopy(threshold.GetOutput())
        self.modifier.apply_labelmap(modifier_image)

    def keep_largest_island(self) -> None:
        self.keep_n_largest_islands(1)

    def split_islands_to_segments(self) -> None:
        if not self.is_active:
            return

        island_image = self.get_island_labelmap()
        label_values = vtkIntArray()
        vtkSlicerSegmentationsModuleLogic.GetAllLabelValues(label_values, island_image)

        modifier_image = self.modifier.create_modifier_labelmap()

        threshold = vtkImageThreshold()
        threshold.SetInputData(island_image)

        # Replace selected segment's labelmap by first island
        initial_label_value = int(label_values.GetTuple1(0))
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

    def get_island_labelmap(self, min_voxel_size: int = 0) -> vtkOrientedImageData:
        source_image_data = self.modifier.get_source_image_data()

        segment_labelmap = self.modifier.get_segment_labelmap(self.modifier.active_segment_id)
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
