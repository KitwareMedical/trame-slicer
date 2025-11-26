from __future__ import annotations

from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode

from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_effect_scissors_widget import SegmentationScissorsPipeline


class SegmentationEffectScissors(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()
        self.set_mode(ModificationMode.RemoveAll)

    def _create_pipeline(
        self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        return SegmentationScissorsPipeline()
