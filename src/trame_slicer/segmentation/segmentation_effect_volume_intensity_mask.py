from __future__ import annotations

from typing import TYPE_CHECKING

from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode
from slicer_core.MRMLCore import vtkMRMLSliceNode

from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_threshold_pipeline import (
    SegmentationThresholdPipeline2D,
    ThresholdParameters,
)
from .threshold_opacity_blinker import ThresholdOpacityBlinker

if TYPE_CHECKING:
    from ..core import SegmentationEditor


class SegmentationEffectVolumeIntensityMask(SegmentationEffect):
    def __init__(self):
        super().__init__()
        self._is_visible = True
        self._opacity_blinker = ThresholdOpacityBlinker()
        self._opacity_blinker.opacity_changed.connect(self._set_mask_opacity)
        self._opacity_blinker.set_opacity_range(0.0, 0.5)

    def _create_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        if isinstance(view_node, vtkMRMLSliceNode):
            return SegmentationThresholdPipeline2D()
        return None

    def set_editor(self, editor: SegmentationEditor) -> None:
        super().set_editor(editor)
        editor.editor_node_modified.connect(self._update_pipeline_parameters)
        editor.active_segment_id_changed.connect(self.trigger_pipeline_parameter_change)
        editor.segmentation_modified.connect(self.trigger_pipeline_parameter_change)

    def set_mask_visible(self, is_visible: bool) -> None:
        if is_visible == self._is_visible:
            return
        self._is_visible = is_visible
        self._update_pipeline_parameters()
        self.parameters_changed()

    def set_mask_enabled(self, is_enabled: bool) -> None:
        if not self.editor_node:
            return
        self.editor_node.SetSourceVolumeIntensityMask(is_enabled)
        if is_enabled:
            self.set_mask_visible(is_enabled)

    def set_mask_range(self, min_value: float, max_value: float) -> None:
        if not self.editor_node:
            return
        self.editor_node.SetSourceVolumeIntensityMaskRange(min_value, max_value)

    def _set_mask_opacity(self, opacity: float) -> None:
        param = self.get_param_proxy()
        param.preview_opacity = opacity

    def get_mask_range(self) -> tuple[float, float]:
        if not self.editor_node:
            return 0.0, 0.0
        return self.editor_node.GetSourceVolumeIntensityMaskRange()

    def is_mask_enabled(self) -> bool:
        if not self.editor_node:
            return False
        return self.editor_node.GetSourceVolumeIntensityMask()

    def _update_pipeline_parameters(self) -> None:
        if not self.editor_node:
            return

        param = self.get_param_proxy()
        param.min_value, param.max_value = self.get_mask_range()
        param.is_visible = self.is_visible
        param.is_hatched = True
        self._opacity_blinker.set_active(self.is_visible)

    def get_param_proxy(self) -> ThresholdParameters:
        from ..utils import create_scripted_module_dataclass_proxy

        return create_scripted_module_dataclass_proxy(ThresholdParameters, self.get_parameter_node(), self._scene)

    @property
    def is_visible(self) -> bool:
        return self._is_visible and self.is_mask_enabled()
