from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode

from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline


class SegmentationEffectScissors(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()
        self.set_mode(ModificationMode.EraseAll)

    def _create_pipeline(
        self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        return None
