from typing import TYPE_CHECKING

from LayerDMLib import vtkMRMLLayerDMScriptedPipeline

from .segment_modifier import SegmentModifier

if TYPE_CHECKING:
    from trame_slicer.views import AbstractViewChild

    from .segmentation_effect import SegmentationEffect


class SegmentationEffectPipeline(vtkMRMLLayerDMScriptedPipeline):
    def __init__(self):
        super().__init__()
        self._effect: SegmentationEffect | None = None
        self._view: AbstractViewChild | None = None
        self._isActive = False

    def GetModifier(self) -> SegmentModifier | None:
        return self._effect.modifier if self._effect else None

    def IsActive(self) -> bool:
        return self._isActive

    def SetSegmentationEffect(self, effect: "SegmentationEffect"):
        self._effect = effect

    def SetView(self, view: "AbstractViewChild"):
        self._view = view

    def SetActive(self, isActive: bool):
        if self._isActive == isActive:
            return

        self._isActive = isActive

        if not self._isActive:
            self.LoseFocus(None)
