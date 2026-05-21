from __future__ import annotations

from enum import Enum, IntFlag, auto

from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode, vtkMRMLSliceNode
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkImagingCore import vtkImageThreshold

from ..utils import create_scripted_module_dataclass_proxy
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_threshold_pipeline import (
    SegmentationThresholdPipeline2D,
    ThresholdParameters,
)
from .threshold_opacity_blinker import ThresholdOpacityBlinker

try:
    from slicer import vtkITKImageThresholdCalculator
except ImportError:
    from vtkITK import vtkITKImageThresholdCalculator

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import SegmentationEditor
    from .segmentation_effect_volume_intensity_mask import (
        SegmentationEffectVolumeIntensityMask,
    )


class AutoThresholdMethod(Enum):
    HUANG = auto()
    INTERMODES = auto()
    ISO_DATA = auto()
    KITTLER_ILLINGWORTH = auto()
    LI = auto()
    MAXIMUM_ENTROPY = auto()
    MOMENTS = auto()
    OTSU = auto()
    RENYI_ENTROPY = auto()
    SHANBHAG = auto()
    TRIANGLE = auto()
    YEN = auto()


class AutoThresholdMode(IntFlag):
    UPPER = auto()
    LOWER = auto()
    MIN = auto()
    MAX = auto()
    MIN_UPPER = MIN | UPPER
    LOWER_MAX = LOWER | MAX


class SegmentationEffectThreshold(SegmentationEffect):
    def __init__(self):
        super().__init__()
        self._opacity_blinker = ThresholdOpacityBlinker()
        self._opacity_blinker.opacity_changed.connect(self._update_preview_opacity)

    def set_editor(self, editor: SegmentationEditor) -> None:
        super().set_editor(editor)
        editor.active_segment_id_changed.connect(self.trigger_pipeline_parameter_change)
        editor.segmentation_modified.connect(self.trigger_pipeline_parameter_change)

    def _create_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        if isinstance(view_node, vtkMRMLSliceNode):
            return SegmentationThresholdPipeline2D()
        return None

    def _update_preview_opacity(self, opacity: float):
        self.get_param_proxy().preview_opacity = opacity

    def set_active(self, is_active: bool):
        super().set_active(is_active)
        self.get_param_proxy().is_visible = is_active
        self._opacity_blinker.set_active(is_active)

    def apply(self):
        if not self.is_active:
            return

        param = self.get_param_proxy()

        # Get source volume image data
        source_image_data = self.modifier.get_source_image_data()

        # Get modifier labelmap
        label_map = self.modifier.create_modifier_labelmap()
        original_image_to_world_matrix = vtkMatrix4x4()
        label_map.GetImageToWorldMatrix(original_image_to_world_matrix)

        # Perform thresholding
        threshold = vtkImageThreshold()
        threshold.SetInputData(source_image_data)
        threshold.ThresholdBetween(param.min_value, param.max_value)
        threshold.SetInValue(1)
        threshold.SetOutValue(0)
        threshold.SetOutputScalarType(label_map.GetScalarType())
        threshold.Update()
        label_map.DeepCopy(threshold.GetOutput())
        self.modifier.apply_labelmap(label_map)

    def auto_threshold(
        self,
        auto_method: AutoThresholdMethod = AutoThresholdMethod.OTSU,
        mode: AutoThresholdMode = AutoThresholdMode.LOWER_MAX,
    ):
        """
        Use auto threshold to set the threshold min / max values.
        Does nothing if the segmentation effect is not currently active.
        """
        if not self.is_active:
            return

        param = self.get_param_proxy()
        calculator = vtkITKImageThresholdCalculator()

        auto_method = {
            AutoThresholdMethod.HUANG: calculator.SetMethodToHuang,
            AutoThresholdMethod.INTERMODES: calculator.SetMethodToIntermodes,
            AutoThresholdMethod.ISO_DATA: calculator.SetMethodToIsoData,
            AutoThresholdMethod.KITTLER_ILLINGWORTH: calculator.SetMethodToKittlerIllingworth,
            AutoThresholdMethod.LI: calculator.SetMethodToLi,
            AutoThresholdMethod.MAXIMUM_ENTROPY: calculator.SetMethodToMaximumEntropy,
            AutoThresholdMethod.MOMENTS: calculator.SetMethodToMoments,
            AutoThresholdMethod.OTSU: calculator.SetMethodToOtsu,
            AutoThresholdMethod.RENYI_ENTROPY: calculator.SetMethodToRenyiEntropy,
            AutoThresholdMethod.SHANBHAG: calculator.SetMethodToShanbhag,
            AutoThresholdMethod.TRIANGLE: calculator.SetMethodToTriangle,
            AutoThresholdMethod.YEN: calculator.SetMethodToYen,
        }.get(auto_method, calculator.SetMethodToOtsu)
        auto_method()

        source_image = self.modifier.get_source_image_data()
        calculator.SetInputData(source_image)
        calculator.Update()

        threshold_value = calculator.GetThreshold()
        vol_min, vol_max = source_image.GetScalarRange()

        if mode & AutoThresholdMode.LOWER:
            param.min_value = threshold_value

        if mode & AutoThresholdMode.UPPER:
            param.max_value = threshold_value

        if mode & AutoThresholdMode.MIN:
            param.min_value = vol_min

        if mode & AutoThresholdMode.MAX:
            param.max_value = vol_max

    def get_param_proxy(self) -> ThresholdParameters:
        return create_scripted_module_dataclass_proxy(ThresholdParameters, self.get_parameter_node(), self._scene)

    def get_threshold_min_max_values(self) -> tuple[float, float]:
        proxy = self.get_param_proxy()
        return proxy.min_value, proxy.max_value

    def set_threshold_min_max_values(self, value: tuple[float, float]):
        proxy = self.get_param_proxy()
        proxy.min_value, proxy.max_value = value

    @property
    def _mask_effect(self) -> SegmentationEffectVolumeIntensityMask | None:
        from .segmentation_effect_volume_intensity_mask import (
            SegmentationEffectVolumeIntensityMask,
        )

        if not self.editor:
            return None
        return self.editor.get_effect(SegmentationEffectVolumeIntensityMask)

    def use_for_volume_intensity_masking(self) -> None:
        if not self._mask_effect:
            return
        threshold_param = self.get_param_proxy()
        self._mask_effect.set_mask_range(threshold_param.min_value, threshold_param.max_value)
        self._mask_effect.set_mask_enabled(True)
