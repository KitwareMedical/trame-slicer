from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from numpy.typing import NDArray
from slicer import vtkMRMLVolumeNode
from vtkmodules.util import numpy_support
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_INT, vtkLookupTable
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkFiltersProgrammable import vtkProgrammableFilter
from vtkmodules.vtkImagingColor import vtkImageMapToRGBA
from vtkmodules.vtkImagingCore import vtkImageMask, vtkImageThreshold
from vtkmodules.vtkImagingStencil import vtkImageStencilToImage
from vtkmodules.vtkRenderingCore import vtkActor2D, vtkImageMapper, vtkRenderer

from ..utils import create_scripted_module_dataclass_proxy
from ..views import SliceView
from .segmentation_effect_pipeline import SegmentationEffectPipeline

if TYPE_CHECKING:
    from slicer import vtkRenderer


@dataclass
class ThresholdParameters:
    min_value: float = 0
    max_value: float = 0
    preview_opacity: float = 0.5
    is_visible: bool = False
    is_hatched: bool = False


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

        # Hatch parameters (not DPI aware)
        self._hatch_line_width = 4
        self._hatch_gap_width = 20
        self._hatch_outline_width = 2

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
        hatch_spacing = self._hatch_line_width + self._hatch_gap_width

        view_node = self._view.get_view_node() if self._view else None
        if not view_node or not param.is_hatched or hatch_spacing <= 0:
            return

        dims = output.GetDimensions()
        if dims[0] == 0 or dims[1] == 0:
            return

        scalars = output.GetPointData().GetScalars()
        arr = numpy_support.vtk_to_numpy(scalars).reshape(dims[1], dims[0])

        # Generate hatching outline
        outline = None
        if self._hatch_outline_width > 0:
            outline = self._HatchOutline(arr, self._hatch_outline_width)

        Y, X = np.ogrid[: dims[1], : dims[0]]
        shift = self._ComputeHatchImageShift(dims, view_node)
        mask = (X + Y + shift[0] + shift[1]) % hatch_spacing < self._hatch_gap_width
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
