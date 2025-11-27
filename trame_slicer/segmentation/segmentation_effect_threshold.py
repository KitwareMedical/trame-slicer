from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum, IntFlag, auto

from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode, vtkMRMLSliceNode
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_INT, vtkLookupTable
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkImagingColor import vtkImageMapToRGBA
from vtkmodules.vtkImagingCore import vtkImageThreshold
from vtkmodules.vtkRenderingCore import vtkActor2D, vtkImageMapper, vtkRenderer

try:
    from vtkITK import vtkITKImageThresholdCalculator
except ImportError:
    from vtkmodules.vtkITK import vtkITKImageThresholdCalculator

from ..utils import create_scripted_module_dataclass_proxy
from ..views import SliceView
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline


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


@dataclass
class ThresholdParameters:
    min_value: float = 0
    max_value: float = 0


class SegmentationThresholdPipeline2D(SegmentationEffectPipeline):
    def __init__(self):
        super().__init__()
        self.lookup_table = vtkLookupTable()
        self.lookup_table.SetRampToLinear()
        self.lookup_table.SetNumberOfTableValues(2)
        self.lookup_table.SetTableRange(0, 1)
        self.lookup_table.SetTableValue(0, 0, 0, 0, 0)
        self.color_mapper = vtkImageMapToRGBA()
        self.color_mapper.SetOutputFormatToRGBA()
        self.color_mapper.SetLookupTable(self.lookup_table)
        self.threshold = vtkImageThreshold()
        self.threshold.SetInValue(1)
        self.threshold.SetOutValue(0)
        self.threshold.SetOutputScalarTypeToUnsignedChar()

        # Feedback actor
        self.mapper = vtkImageMapper()
        self.dummy_image = vtkImageData()
        self.dummy_image.AllocateScalars(VTK_UNSIGNED_INT, 1)
        self.mapper.SetInputData(self.dummy_image)
        self.actor = vtkActor2D()
        self.actor.VisibilityOff()
        self.actor.SetMapper(self.mapper)
        self.mapper.SetColorWindow(255)
        self.mapper.SetColorLevel(128)

        # Setup pipeline
        self.color_mapper.SetInputConnection(self.threshold.GetOutputPort())
        self.mapper.SetInputConnection(self.color_mapper.GetOutputPort())

        # Preview coroutine
        self.preview_update_period_s = 0.2
        self.preview_steps = 6
        self.preview_state = 0
        self.preview_direction = 1
        loop = asyncio.get_event_loop()
        self.preview_task = loop.create_task(self._UpdatePreviewState())

    async def _UpdatePreviewState(self):
        while True:
            await asyncio.sleep(self.preview_update_period_s)
            self.preview_state += self.preview_direction
            if self.preview_state > self.preview_steps or self.preview_state < 0:
                self.preview_direction *= -1
                self.preview_state += self.preview_direction
            self.preview_state = max(0, min(self.preview_steps, self.preview_state))
            self._UpdateThreshold()

    def OnRendererAdded(self, renderer: vtkRenderer | None) -> None:
        super().OnRendererAdded(renderer)
        if renderer:
            renderer.AddViewProp(self.actor)

    def OnRendererRemoved(self, renderer: vtkRenderer) -> None:
        super().OnRendererRemoved(renderer)
        if renderer and renderer.HasViewProp(self.actor):
            renderer.RemoveViewProp(self.actor)

    def SetActive(self, isActive: bool):
        super().SetActive(isActive)
        self.actor.SetVisibility(isActive)
        self.RequestRender()

    def OnEffectParameterUpdate(self):
        super().OnEffectParameterUpdate()
        if not self.GetEffectParameterNode():
            return
        self._UpdateThreshold()

    def _UpdateThreshold(self):
        if not self.IsActive():
            return

        param = create_scripted_module_dataclass_proxy(
            ThresholdParameters, self.GetEffectParameterNode(), self.GetScene()
        )

        active_id = self.GetModifier().active_segment_id
        if segmentation := self.GetSegmentation():
            opacity = 0.5 + 0.5 * self.preview_state / self.preview_steps
            r, g, b = segmentation.get_segment_properties(active_id).color
            self.lookup_table.SetTableValue(1, r, g, b, opacity)

        self.threshold.ThresholdBetween(param.min_value, param.max_value)
        self.OnViewModified()
        self.threshold.Update()
        self.RequestRender()

    def SetView(self, view: SliceView):
        if self._view:
            self._view.modified.disconnect(self.OnViewModified)
        super().SetView(view)
        if self._view:
            self._view.modified.connect(self.OnViewModified)

    def OnViewModified(self, *_):
        if not self._view or not self.GetModifier():
            return

        self.threshold.SetInputConnection(
            self._view.get_volume_layer_logic(self.GetModifier().volume_node).GetReslice().GetOutputPort()
        )


class SegmentationEffectThreshold(SegmentationEffect):
    def _create_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        if isinstance(view_node, vtkMRMLSliceNode):
            return SegmentationThresholdPipeline2D()
        return None

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

    def use_for_volume_intensity_masking(self):
        if not self.is_active:
            return

        param = self.get_param_proxy()
        self.modifier.set_source_volume_intensity_mask_range(param.min_value, param.max_value)
        self.modifier.set_source_volume_intensity_mask_enabled(True)

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
