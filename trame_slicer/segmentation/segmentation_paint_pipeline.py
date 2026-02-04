from __future__ import annotations

from typing import Callable

from slicer import (
    vtkMRMLAbstractWidget,
    vtkMRMLInteractionEventData,
    vtkMRMLModelNode,
)
from vtkmodules.vtkCommonCore import vtkCommand

from trame_slicer.utils import (
    ClosestToCameraPicker,
    create_scripted_module_dataclass_proxy,
)
from trame_slicer.views import SliceView, ThreeDView

from .paint_effect_parameters import PaintEffectParameters
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_paint_widget import (
    SegmentationPaintWidget,
    SegmentationPaintWidget2D,
    SegmentationPaintWidget3D,
)


class SegmentationPaintPipeline(SegmentationEffectPipeline):
    def __init__(self) -> None:
        super().__init__()

        self.widget: SegmentationPaintWidget | None = None

        # Events we may consume and how we consume them
        self._supported_events: dict[int, Callable] = {
            int(vtkCommand.MouseMoveEvent): self._MouseMoved,
            int(vtkCommand.LeftButtonPressEvent): self._LeftButtonPress,
            int(vtkCommand.LeftButtonReleaseEvent): self._LeftButtonRelease,
        }

        self._modelNode: vtkMRMLModelNode | None = None
        self._feedbackNode: vtkMRMLModelNode | None = None

    def OnEffectParameterUpdate(self):
        if not self.GetEffectParameterNode() or not self.GetScene():
            return

        proxy = create_scripted_module_dataclass_proxy(
            PaintEffectParameters, self.GetEffectParameterNode(), self.GetScene()
        )
        self._modelNode = proxy.brush_model_node
        self._feedbackNode = proxy.paint_feedback_model_node
        if self.widget:
            self.widget.update_paint_parameters(proxy)

    def _UpdateFeedbackConnection(self):
        if self._modelNode:
            self._modelNode.SetPolyDataConnection(self.widget.get_brush_polydata_port())

        if self._feedbackNode:
            self._feedbackNode.SetPolyDataConnection(self.widget.get_feedback_polydata_port())

    def CreateWidget(self):
        raise NotImplementedError()

    def SetActive(self, isActive: bool):
        super().SetActive(isActive)
        self._SetFeedbackVisible(isActive)
        if isActive and not self.widget:
            self.CreateWidget()
            self.OnEffectParameterUpdate()

        if not self.widget:
            return

        self.widget.set_modifier(self._effect.modifier)

    def IsSupportedEvent(self, event_data: vtkMRMLInteractionEventData):
        return event_data.GetType() in self._supported_events

    def ProcessInteractionEvent(self, event_data: vtkMRMLInteractionEventData) -> bool:
        self._SetFeedbackVisible(True)
        self._UpdateFeedbackConnection()
        if not self.widget:
            return False

        if not self.IsSupportedEvent(event_data):
            return False

        callback = self._supported_events.get(event_data.GetType())
        return callback(event_data) if callback is not None else False

    def CanProcessInteractionEvent(self, eventData: vtkMRMLInteractionEventData) -> tuple[bool, float]:
        can_process = self.widget and self.IsActive() and self.IsSupportedEvent(eventData)
        return can_process, 0

    def _LeftButtonPress(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_painting():
            return True

        self.widget.start_painting()
        self._PaintAtEventLocation(event_data)
        self.RequestRender()
        return True

    def LoseFocus(self, eventData: vtkMRMLInteractionEventData | None) -> None:
        super().LoseFocus(eventData)
        self._LeftButtonRelease(eventData)
        self._SetFeedbackVisible(False)

    def _LeftButtonRelease(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_painting():
            self.widget.stop_painting()
            self.RequestRender()
        return True

    def _MouseMoved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        self._PaintAtEventLocation(event_data)
        self.RequestRender()
        return True

    def _PaintAtEventLocation(self, event_data: vtkMRMLInteractionEventData) -> bool:
        raise NotImplementedError()

    def GetWidgetState(self) -> int:
        if not self.widget or not self.widget.is_painting():
            return super().GetWidgetState()

        return vtkMRMLAbstractWidget.WidgetStateUser

    def _SetFeedbackVisible(self, isVisible):
        self._SetVisible(self._modelNode, isVisible)
        self._SetVisible(self._feedbackNode, isVisible)

    @classmethod
    def _SetVisible(cls, modelNode, isVisible):
        if not modelNode:
            return
        displayNode = modelNode.GetDisplayNode()
        if not displayNode:
            return
        displayNode.SetVisibility(isVisible)


class SegmentationPaintPipeline2D(SegmentationPaintPipeline):
    def __init__(self) -> None:
        super().__init__()

        self._supported_events: dict[int, Callable] = {
            **self._supported_events,
            int(vtkCommand.MouseWheelBackwardEvent): self._MouseWheelBackward,
            int(vtkCommand.MouseWheelForwardEvent): self._MouseWheelForward,
        }

    def CreateWidget(self):
        if self.widget is not None or not isinstance(self._view, SliceView):
            return

        self.widget = SegmentationPaintWidget2D(self._view)

    def _MouseWheelForward(self, event_data):
        if self._view.interactor().GetShiftKey():
            self._effect.increase_brush_size()
            self._PaintAtEventLocation(event_data)
            self.RequestRender()
            return False
        return True

    def _MouseWheelBackward(self, event_data):
        if self._view.interactor().GetShiftKey():
            self._effect.decrease_brush_size()
            self._PaintAtEventLocation(event_data)
            self.RequestRender()
            return False
        return True

    def _PaintAtEventLocation(self, event_data: vtkMRMLInteractionEventData) -> bool:
        self.widget.update_widget_position(event_data.GetWorldPosition())
        return True


class SegmentationPaintPipeline3D(SegmentationPaintPipeline):
    def __init__(self):
        super().__init__()
        self._picker = ClosestToCameraPicker()
        self._last_pick_position = None

    def Pick(self, event_data):
        self._last_pick_position = self._picker.pick(
            event_data.GetDisplayPosition(), self.GetRenderer(), self.GetRenderer().GetActiveCamera()
        )

    def HasLastPickPosition(self):
        return self._last_pick_position is not None

    def IsSupportedEvent(self, event_data: vtkMRMLInteractionEventData):
        if not super().IsSupportedEvent(event_data):
            return False
        self.Pick(event_data)
        return self.HasLastPickPosition()

    def CreateWidget(self):
        if self.widget is not None or not isinstance(self._view, ThreeDView):
            return

        self.widget = SegmentationPaintWidget3D(self._view)

    def _PaintAtEventLocation(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        self.widget.update_widget_position(self._last_pick_position)
        return True
