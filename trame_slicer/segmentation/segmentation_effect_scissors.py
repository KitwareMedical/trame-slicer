from __future__ import annotations

from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode

from trame_slicer.segmentation import ModificationMode
from trame_slicer.utils import create_scripted_module_dataclass_proxy

from .scissors_effect_parameters import ScissorsEffectParameters
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_effect_scissors_widget import (
    ScissorsSegmentationOperation,
    ScissorsSegmentationSliceCut,
    SegmentationScissorsPipeline,
)


class SegmentationEffectScissors(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()
        self.set_mode(ModificationMode.RemoveAll)

    def _create_pipeline(
        self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        return SegmentationScissorsPipeline()

    def _get_proxy(self) -> ScissorsEffectParameters:
        return create_scripted_module_dataclass_proxy(ScissorsEffectParameters, self._param_node, self._scene)

    def set_symmetric_distance(self, symmetric_distance: float):
        proxy = self._get_proxy()
        proxy.symmetric_distance = symmetric_distance

    def set_operation(self, operation: ScissorsSegmentationOperation):
        proxy = self._get_proxy()
        if operation in [ScissorsSegmentationOperation.ERASE_INSIDE, ScissorsSegmentationOperation.ERASE_OUTSIDE]:
            self.set_mode(ModificationMode.RemoveAll)
        else:
            self.set_mode(ModificationMode.Add)
        proxy.operation = operation

    def set_cut_mode(self, cut_mode: ScissorsSegmentationSliceCut):
        proxy = self._get_proxy()
        proxy.cut_mode = cut_mode
