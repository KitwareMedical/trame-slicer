from __future__ import annotations

from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode

from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline


class SegmentationEffectNoTool(SegmentationEffect):
    """
    Empty implementation when no segmentation effect is selected.
    """

    def _create_pipeline(
        self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        return None
