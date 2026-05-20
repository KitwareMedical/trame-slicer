from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum, IntFlag, auto

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from numpy.typing import NDArray
from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode, vtkMRMLSliceNode
from slicer_core import vtkMRMLVolumeNode
from undo_stack import Signal
from vtkmodules.util import numpy_support
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_INT, vtkLookupTable
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkFiltersProgrammable import vtkProgrammableFilter
from vtkmodules.vtkImagingColor import vtkImageMapToRGBA
from vtkmodules.vtkImagingCore import vtkImageMask, vtkImageThreshold
from vtkmodules.vtkImagingStencil import vtkImageStencilToImage
from vtkmodules.vtkRenderingCore import vtkActor2D, vtkImageMapper, vtkRenderer

from ..utils import create_scripted_module_dataclass_proxy
from ..views import SliceView
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline

try:
    from slicer import vtkITKImageThresholdCalculator
except ImportError:
    from vtkITK import vtkITKImageThresholdCalculator

from typing import TYPE_CHECKING, Any

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


@dataclass
class ThresholdParameters:
    min_value: float = 0
    max_value: float = 0
    preview_opacity: float = 0.5
    is_visible: bool = False
    hatch: bool = False
    hatch_line_width: int = 4
    hatch_gap_width: int = 20
    hatch_outline_width: int = 2


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

        self.stencil_to_image = vtkImageStencilToImage()
        self.volume_bounds_mask = vtkImageMask()

        self.hatch_filter = vtkProgrammableFilter()
        self.hatch_filter.SetExecuteMethod(self._ExecuteHatch)
        self.hatch_filter.SetInputConnection(self.volume_bounds_mask.GetOutputPort())

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
        self.color_mapper.SetInputConnection(self.hatch_filter.GetOutputPort())
        self.mapper.SetInputConnection(self.color_mapper.GetOutputPort())

        self._volume_node = None

    def OnRendererAdded(self, renderer: vtkRenderer | None) -> None:
        super().OnRendererAdded(renderer)
        if renderer:
            renderer.AddViewProp(self.actor)

    def OnRendererRemoved(self, renderer: vtkRenderer) -> None:
        super().OnRendererRemoved(renderer)
        if renderer and renderer.HasViewProp(self.actor):
            renderer.RemoveViewProp(self.actor)

    def OnEffectParameterUpdate(self):
        super().OnEffectParameterUpdate()
        if not self.GetEffectParameterNode():
            return
        self._UpdateThreshold()

    def _UpdateThreshold(self):
        active_color = self._GetActiveColor()
        if active_color is None:
            self.actor.SetVisibility(False)
            return

        param = create_scripted_module_dataclass_proxy(
            ThresholdParameters, self.GetEffectParameterNode(), self.GetScene()
        )

        self._UpdateActiveVolumeNode()
        self.actor.SetVisibility(param.is_visible)

        self.lookup_table.SetTableValue(1, *active_color, param.preview_opacity)

        self.threshold.ThresholdBetween(param.min_value, param.max_value)
        self.OnViewModified()
        self.threshold.Update()
        self.RequestRender()

    def _GetActiveColor(self) -> list[float] | None:
        if not self.GetModifier() or not self.GetSegmentation():
            return None

        active_id = self.GetModifier().active_segment_id
        properties = self.GetSegmentation().get_segment_properties(active_id)
        if not properties:
            return None

        return properties.color

    def _ExecuteHatch(self):
        input_data = self.hatch_filter.GetInputDataObject(0, 0)
        output = self.hatch_filter.GetOutput()
        output.ShallowCopy(input_data)

        param = create_scripted_module_dataclass_proxy(
            ThresholdParameters, self._effect.get_parameter_node(), self.GetScene()
        )
        hatch_spacing = param.hatch_line_width + param.hatch_gap_width

        view_node = self._view.get_view_node() if self._view else None
        if not view_node or not param.hatch or hatch_spacing <= 0:
            return

        dims = output.GetDimensions()
        if dims[0] == 0 or dims[1] == 0:
            return

        scalars = output.GetPointData().GetScalars()
        arr = numpy_support.vtk_to_numpy(scalars).reshape(dims[1], dims[0])

        # Generate hatching outline
        outline = None
        if param.hatch_outline_width > 0:
            outline = self._HatchOutline(arr, param.hatch_outline_width)

        Y, X = np.ogrid[: dims[1], : dims[0]]
        shift = self._ComputeHatchImageShift(dims, view_node)
        mask = (X + Y + shift[0] + shift[1]) % hatch_spacing < param.hatch_gap_width
        arr[mask] = 0

        if outline is not None:
            arr[outline] = 1

    @classmethod
    def _ComputeHatchImageShift(cls, dims, view_node: Any | None) -> list[int]:
        origin = view_node.GetXYZOrigin()
        fov = view_node.GetFieldOfView()

        shift = []
        for i in range(2):
            spacing = fov[i] / dims[i]
            image_origin = origin[i] - fov[i] / 2.0
            shift.append(round(image_origin / spacing))

        return shift

    @classmethod
    def _HatchOutline(cls, mask: NDArray, radius_px: int) -> NDArray:
        mask = mask.astype(bool)

        # Erode mask by input kernel radius
        k = 2 * radius_px + 1
        kernel = np.ones((k, k), dtype=int)
        windows = sliding_window_view(mask, (k, k))
        eroded = windows.sum(axis=(2, 3)) == kernel.sum()
        pad = radius_px
        eroded = np.pad(eroded, pad, mode="constant")

        return mask & ~eroded

    def SetView(self, view: SliceView):
        if self._view:
            self._view.modified.disconnect(self.OnViewModified)
        super().SetView(view)
        if self._view:
            self._view.modified.connect(self.OnViewModified)

    def OnViewModified(self, *_):
        if not self._view or not self.GetModifier():
            return

        reslice = self._view.get_volume_layer_logic(self._ActiveVolumeNode).GetReslice()
        reslice.GenerateStencilOutputOn()
        self.stencil_to_image.SetInputConnection(reslice.GetStencilOutputPort())
        self.threshold.SetInputConnection(reslice.GetOutputPort())
        self.volume_bounds_mask.SetInputConnection(self.threshold.GetOutputPort())
        self.volume_bounds_mask.SetInputConnection(1, self.stencil_to_image.GetOutputPort())

    @property
    def _ActiveVolumeNode(self) -> vtkMRMLVolumeNode | None:
        return self.GetModifier().volume_node if self.GetModifier() else None

    def _UpdateActiveVolumeNode(self) -> None:
        if self._volume_node == self._ActiveVolumeNode:
            return

        self._MoveActorToRendererTop()
        self._volume_node = self._ActiveVolumeNode

    def _MoveActorToRendererTop(self):
        """
        Trigger adding / removing actor from the renderer to be placed correctly with respect to volume display.
        Hack to be in the same renderer layer as the volume slice display while moving the feedback to the top.
        """
        self.OnRendererRemoved(self.GetRenderer())
        self.OnRendererAdded(self.GetRenderer())


class ThresholdOpacityBlinker:
    opacity_changed = Signal(float)

    def __init__(self):
        self._blink_opacity_min = 0.5
        self._blink_opacity_max = 1.0
        self._preview_update_period_s = 0.2
        self._preview_steps = 6
        self._preview_state = 0
        self._preview_direction = 1
        self._preview_task: asyncio.Task | None = None

    def set_active(self, is_active: bool) -> None:
        if not is_active:
            self.stop()
        else:
            self.start()

    def set_opacity_range(self, low: float, high: float):
        self._blink_opacity_min = low
        self._blink_opacity_max = high

    def start(self):
        if self._preview_task is None:
            loop = asyncio.get_event_loop()
            self._preview_task = loop.create_task(self._update_preview_state())

    def stop(self):
        if self._preview_task is not None:
            self._preview_task.cancel()
            self._preview_task = None
            self._preview_state = 0

    async def _update_preview_state(self):
        while True:
            await asyncio.sleep(self._preview_update_period_s)
            self._preview_state += self._preview_direction
            if self._preview_state >= self._preview_steps or self._preview_state < 0:
                self._preview_direction *= -1
                self._preview_state += 2 * self._preview_direction
            self._preview_state = max(0, min(self._preview_steps - 1, self._preview_state))
            opacity_range = self._blink_opacity_max - self._blink_opacity_min
            opacity = self._blink_opacity_min + opacity_range * self._preview_state / (self._preview_steps - 1)
            self.opacity_changed(opacity)


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
