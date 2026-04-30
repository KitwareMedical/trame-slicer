from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLNode,
    vtkMRMLScriptedModuleNode,
    vtkMRMLSliceNode,
)

from .segmentation_effect_threshold import SegmentationThresholdPipeline2D


class _MaskedVolumeParameterNode(vtkMRMLScriptedModuleNode):
    VISIBILITY_KEY = "Visibility"
    COLOR_KEY = "Color"
    RANGE_MIN_KEY = "RangeMin"
    RANGE_MAX_KEY = "RangeMax"

    def set_visibility(self, visibility: bool):
        self.SetParameter(self.VISIBILITY_KEY, str(int(visibility)))

    def get_visibility(self) -> bool:
        try:
            return bool(int(self.GetParameter(self.VISIBILITY_KEY)))
        except ValueError:
            return False

    def set_color(self, r: float, g: float, b: float, a: float):
        self.SetParameter(self.COLOR_KEY, "_".join([str(c) for c in [r, g, b, a]]))

    def get_color(self) -> tuple[float, float, float, float] | None:
        try:
            return [float(c) for c in self.GetParameter(self.COLOR_KEY).split("_")]
        except ValueError:
            return None

    def set_range(self, low: float, high: float):
        self.set_low_value(low)
        self.set_high_value(high)

    def get_range(self) -> tuple[float | None, float | None]:
        return (self.get_low_value(), self.get_high_value())

    def set_low_value(self, low: float):
        self.SetParameter(self.RANGE_MIN_KEY, str(low))

    def get_low_value(self) -> float | None:
        try:
            return float(self.GetParameter(self.RANGE_MIN_KEY))
        except ValueError:
            return None

    def set_high_value(self, high: float):
        self.SetParameter(self.RANGE_MAX_KEY, str(high))

    def get_high_value(self) -> float | None:
        try:
            return float(self.GetParameter(self.RANGE_MAX_KEY))
        except ValueError:
            return None


class SegmentationMaskedVolumeIntensityRangePipeline(SegmentationThresholdPipeline2D):
    def __init__(self, segmentationDisplayManager):
        super().__init__()

        self._segmentation_display_manager = segmentationDisplayManager

    @classmethod
    def CreateParameterNode(cls) -> _MaskedVolumeParameterNode:
        node = _MaskedVolumeParameterNode()
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

    def _GetColor(self) -> tuple[float, float, float, float] | None:
        return self.GetEffectParameterNode().get_color()

    def _GetRange(self) -> tuple[float | None, float | None]:
        active = self._segmentation_display_manager.get_source_volume_intensity_mask()
        return self.GetEffectParameterNode().get_range() if active else (-9999.0, 9999.0)

    def OnEffectParameterUpdate(self):
        self.OnViewModified()
        low, high = self._GetRange()
        if (
            low is not None
            and high is not None
            and (self.threshold.GetLowerThreshold() != low or self.threshold.GetUpperThreshold() != high)
        ):
            self.threshold.ThresholdBetween(low, high)
            self.threshold.Update()
        color = self._GetColor()
        if color is not None:
            self.lookup_table.SetTableValue(1, self._GetColor())
        self.SetActive(self.GetEffectParameterNode().get_visibility())

    @classmethod
    def _GetClassName(cls) -> str:
        """
        Convenience method to get the name of the current class.
        This method will return the actual class name for inheriting classes.
        """
        return cls.__name__
