from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode, vtkMRMLSliceNode

from .scissors_effect_parameters import ScissorsEffectFillMode, ScissorsEffectRangeMode
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_effect_scissors import SegmentationEffectScissors


class SegmentationEffectDraw(SegmentationEffectScissors):
    def __init__(self):
        super().__init__()
        self.set_symmetric_distance(0.0)
        self.set_fill_mode(ScissorsEffectFillMode.FILL_INSIDE)
        self.set_range_mode(ScissorsEffectRangeMode.SYMMETRIC)

    def _create_pipeline(
        self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        if isinstance(_view_node, vtkMRMLSliceNode):
            from .segmentation_effect_scissors_widget import (
                SegmentationScissorsPipeline,
            )

            return SegmentationScissorsPipeline()
        return None  # Interaction in 3D not supported
