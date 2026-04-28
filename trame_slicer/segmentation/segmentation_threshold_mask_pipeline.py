from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLNode,
    vtkMRMLScriptedModuleNode,
    vtkMRMLSliceNode,
)

from .segmentation_effect_threshold import SegmentationThresholdPipeline2D


class SegmentationThresholdMaskPipeline(SegmentationThresholdPipeline2D):
    def __init__(self, segmentationDisplayManager):
        super().__init__()

        self._segmentation_display_manager = segmentationDisplayManager

    @classmethod
    def CreateParameterNode(cls) -> vtkMRMLScriptedModuleNode:
        node = vtkMRMLScriptedModuleNode()
        node.SetAttribute("PipelineType", cls._GetClassName())
        node.SetSaveWithScene(False)
        return node

    @classmethod
    def IsPipelineNode(cls, node: vtkMRMLNode) -> bool:
        """
        Returns True if the input vktMRMLNode is a scripted node and has the pipeline type attribute matching the
        current pipeline class.
        """
        return isinstance(node, vtkMRMLScriptedModuleNode) and node.GetAttribute("PipelineType") == cls._GetClassName()

    @classmethod
    def TryCreatePipeline(
        cls,
        viewNode: vtkMRMLAbstractViewNode,
        node: vtkMRMLNode,
        segmentationDisplayManager,
    ):
        if not cls.IsPipelineNode(node) or not isinstance(viewNode, vtkMRMLSliceNode):
            return None

        return cls(segmentationDisplayManager)

    def _GetColor(self) -> tuple[float, float, float, float]:
        return self._segmentation_display_manager.get_threshold_mask_color()

    def _GetRange(self) -> tuple[float, float]:
        active = self._segmentation_display_manager.get_source_volume_intensity_mask()
        return (
            self._segmentation_display_manager.get_source_volume_intensity_mask_range() if active else (-9999.0, 9999.0)
        )

    def RequestRender(self):
        self.OnViewModified()
        low, high = self._GetRange()
        if self.threshold.GetLowerThreshold() != low or self.threshold.GetUpperThreshold() != high:
            self.threshold.ThresholdBetween(low, high)
            self.threshold.Update()
        self.lookup_table.SetTableValue(1, self._GetColor())
        super().RequestRender()

    @classmethod
    def _GetClassName(cls) -> str:
        """
        Convenience method to get the name of the current class.
        This method will return the actual class name for inheriting classes.
        """
        return cls.__name__
