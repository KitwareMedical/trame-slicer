from __future__ import annotations

from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode

from .segmentation_effect import SegmentationEffect
from .segmentation_effect_draw_widget import SegmentationDrawPipeline
from .segmentation_effect_pipeline import SegmentationEffectPipeline


class SegmentationEffectDraw(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()

    def _create_pipeline(
        self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        return SegmentationDrawPipeline()
