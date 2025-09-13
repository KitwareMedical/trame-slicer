from typing import Any, Callable

from slicer import (
    vtkMRMLAbstractWidget,
    vtkMRMLInteractionEventData,
    vtkMRMLModelNode,
    vtkMRMLNode,
)
from vtkmodules.vtkCommonCore import vtkCommand, vtkObject

from trame_slicer.utils import (
    ClosestToCameraPicker,
    create_scripted_module_dataclass_proxy,
)
from trame_slicer.views import SliceView, ThreeDView

from .brush_model import PaintEffectParameters
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_paint_widget import SegmentationPaintWidget
from .segmentation_paint_widget_2d import SegmentationPaintWidget2D
from .segmentation_paint_widget_3d import SegmentationPaintWidget3D


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

    def OnUpdate(self, obj: vtkObject, _eventId: int, _callData: Any | None) -> None:
        if obj == self.GetDisplayNode():
            self._UpdateModelNodes()

    def SetDisplayNode(self, displayNode: vtkMRMLNode) -> None:
        super().SetDisplayNode(displayNode)
        self._UpdateModelNodes()

    def _UpdateModelNodes(self):
        if not self.GetDisplayNode() or not self.GetScene():
            return

        proxy = create_scripted_module_dataclass_proxy(PaintEffectParameters, self.GetDisplayNode(), self.GetScene())
        self._modelNode = proxy.brush_model_node
        self._feedbackNode = proxy.paint_feedback_model_node

    def CreateWidget(self):
        raise NotImplementedError()

    def SetActive(self, isActive: bool):
        super().SetActive(isActive)

        if isActive and not self.widget:
            self.CreateWidget()

        if not self.widget:
            return

        self.widget.set_modifier(self._effect.modifier)

    def IsSupportedEvent(self, event_data: vtkMRMLInteractionEventData):
        return event_data.GetType() in self._supported_events

    def ProcessInteractionEvent(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if not self.widget:
            return False

        if not self.IsSupportedEvent(event_data):
            return False

        callback = self._supported_events.get(event_data.GetType())
        didProcess = callback(event_data) if callback is not None else False
        self._UpdateWidgetDisplay()
        return didProcess

    def _UpdateWidgetDisplay(self):
        if not self._modelNode or not self._feedbackNode:
            return

        self._modelNode.SetAndObservePolyData(self.widget.get_brush_polydata())
        self._feedbackNode.SetAndObservePolyData(self.widget.get_feedback_polydata())

    def CanProcessInteractionEvent(self, eventData: vtkMRMLInteractionEventData) -> tuple[bool, float]:
        can_process = self.widget and self.IsActive() and self.IsSupportedEvent(eventData)
        return can_process, 0

    def _LeftButtonPress(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_painting():
            return False

        self.widget.start_painting()
        self._PaintAtEventLocation(event_data)
        self.RequestRender()
        return True

    def _LeftButtonRelease(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_painting():
            self.widget.stop_painting()
            self.RequestRender()

        # Always let other interactor and displayable managers do whatever they want
        return False

    def _MouseMoved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        self._PaintAtEventLocation(event_data)
        self.RequestRender()
        return self.widget.is_painting()

    def _PaintAtEventLocation(self, event_data: vtkMRMLInteractionEventData) -> bool:
        raise NotImplementedError()

    def GetWidgetState(self) -> int:
        if not self.widget or not self.widget.is_painting():
            return super().GetWidgetState()

        return vtkMRMLAbstractWidget.WidgetStateUser


class SegmentationPaintPipeline2D(SegmentationPaintPipeline):
    def CreateWidget(self):
        if self.widget is not None or not isinstance(self._view, SliceView):
            return

        self.widget = SegmentationPaintWidget2D(self._view)

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
        if self._last_pick_position is None and self.widget:
            self.widget.invalidate_last_position()

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
