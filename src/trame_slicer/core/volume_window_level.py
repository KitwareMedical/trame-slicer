from __future__ import annotations

from slicer import vtkMRMLVolumeDisplayNode, vtkMRMLVolumeNode
from vtkmodules.vtkImagingStatistics import vtkImageHistogramStatistics


class VolumeWindowLevel:
    """
    Collection of helper functions to update a volume's window / level
    """

    @classmethod
    def get_volume_auto_min_max_range(cls, volume_node: vtkMRMLVolumeNode) -> tuple[float, float]:
        imageData = volume_node.GetImageData()

        stats = vtkImageHistogramStatistics()
        stats.SetAutoRangePercentiles(0.1, 99.9)
        stats.SetAutoRangeExpansionFactors(0, 0)
        stats.SetInputData(imageData)
        stats.Update()
        return stats.GetAutoRange()

    @classmethod
    def get_volume_scalar_range(cls, volume_node: vtkMRMLVolumeNode) -> tuple[float, float]:
        return volume_node.GetImageData().GetScalarRange()

    @classmethod
    def set_volume_node_window_level(cls, volume_node: vtkMRMLVolumeNode, window: float, level: float) -> None:
        d_node = cls.get_volume_display_node(volume_node)
        d_node.SetAutoWindowLevel(0)
        d_node.SetWindowLevel(window, level)

    @classmethod
    def set_volume_node_display_min_max_range(
        cls, volume_node: vtkMRMLVolumeNode, min_value: float, max_value: float
    ) -> None:
        cls.set_volume_node_window_level(volume_node, *cls.min_max_to_window_level(min_value, max_value))

    @classmethod
    def get_volume_display_range(cls, volume_node: vtkMRMLVolumeNode) -> tuple[float, float]:
        d_node = cls.get_volume_display_node(volume_node)
        return cls.window_level_to_min_max(d_node.GetWindow(), d_node.GetLevel())

    @classmethod
    def window_level_to_min_max(cls, window: float, level: float) -> tuple[float, float]:
        return level - window / 2, level + window / 2

    @classmethod
    def min_max_to_window_level(cls, min_value: float, max_value: float) -> tuple[float, float]:
        if min_value > max_value:
            min_value, max_value = max_value, min_value

        window = max_value - min_value
        level = (max_value + min_value) / 2.0
        return window, level

    @classmethod
    def get_volume_display_node(cls, volume_node: vtkMRMLVolumeNode) -> vtkMRMLVolumeDisplayNode:
        d_node = volume_node.GetDisplayNode()
        if d_node is None:
            volume_node.CreateDefaultDisplayNodes()
            d_node = volume_node.GetDisplayNode()
        return d_node
