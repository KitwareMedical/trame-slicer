from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLInteractionEventData,
    vtkMRMLNode,
)
from undo_stack.signal import Signal
from vtkmodules.vtkCommonCore import vtkCommand, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkRenderingCore import (
    vtkActor2D,
    vtkPolyDataMapper2D,
    vtkProp,
    vtkRenderer,
)

from .scissors_effect_parameters import BrushInteractionMode
from .segment_modifier import SegmentModifier
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_effect_scissors import SegmentationEffectScissors


class _IDrawer(ABC):
    @abstractmethod
    def add_point(self, x: float, y: float) -> None:
        pass

    @abstractmethod
    def set_visible(self, is_visible: bool) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def get_props(self) -> list[vtkProp]:
        pass


class _OpenCurveDrawer(_IDrawer):
    """
    Stores and manipulates data related to drawing an open poly line in 2D
    """

    def __init__(self, color: tuple[float, float, float], point_size: float, line_width: float):
        self.points = vtkPoints()
        self.lines = vtkCellArray()
        self.vertices = vtkCellArray()
        self.polydata = vtkPolyData()
        self.polydata.SetLines(self.lines)
        self.polydata.SetVerts(self.vertices)
        self.polydata.SetPoints(self.points)

        self.mapper = vtkPolyDataMapper2D()
        self.mapper.SetInputData(self.polydata)
        self.actor = vtkActor2D()
        self.actor.SetMapper(self.mapper)
        self.actor.SetVisibility(False)

        props = self.actor.GetProperty()
        props.SetColor(*color)
        props.SetPointSize(point_size)
        props.SetLineWidth(line_width)

    def add_point(self, x: float, y: float) -> None:
        self.points.InsertNextPoint(x, y, 1.0)
        if self.n_points > 1:
            self.lines.InsertNextCell(2, [self.n_points - 1, self.n_points - 2])
        self.vertices.InsertNextCell(1, [self.n_points - 1])
        self.points.Modified()

    def set_point(self, i_pt: int, x: float, y: float) -> None:
        while self.n_points <= i_pt:
            self.add_point(x, y)
        self.points.SetPoint(i_pt, x, y, 0)
        self.points.Modified()

    def set_visible(self, visibility: bool) -> None:
        self.actor.SetVisibility(visibility)

    def reset(self) -> None:
        self.points.SetNumberOfPoints(0)
        self.vertices.Reset()
        self.lines.Reset()
        self.polydata.Modified()

    def get_props(self) -> list[vtkProp]:
        return [self.actor]

    @property
    def n_points(self) -> int:
        return self.points.GetNumberOfPoints()


class _PreviewDrawer(_IDrawer):
    """
    Store and manipulates two lines representing the closing and preview lines of an ongoing 2D drawing
    """

    def __init__(self):
        self._close_line = _OpenCurveDrawer((0.8, 0.8, 0.0), 0.0, 2.0)
        self._preview_line = _OpenCurveDrawer((1.0, 1.0, 0.0), 4.0, 2.0)

    def preview_point(self, x: int, y: int) -> None:
        if self._close_line.n_points:
            self._close_line.set_point(1, x, y)
        self._preview_line.set_point(0, x, y)

    def add_point(self, x: int, y: int) -> None:
        if not self._close_line.n_points:
            self._close_line.set_point(0, x, y)
        self._preview_line.set_point(1, x, y)

    def set_visible(self, visibility: bool) -> None:
        self._close_line.set_visible(visibility)
        self._preview_line.set_visible(visibility)

    def get_props(self) -> list[vtkProp]:
        return [*self._close_line.get_props(), *self._preview_line.get_props()]

    def reset(self) -> None:
        self._close_line.reset()
        self._preview_line.reset()


class ScissorsPolygonBrush:
    """Display the scissors as 2D lines"""

    def __init__(self):
        super().__init__()
        self._open_curve = _OpenCurveDrawer((1.0, 1.0, 0.0), 4.0, 2.0)
        self._preview = _PreviewDrawer()

    def set_visible(self, visible: bool):
        self._open_curve.set_visible(visible)
        self._preview.set_visible(visible)

    def preview_point(self, x: int, y: int) -> None:
        self._preview.preview_point(x, y)

    def add_point(self, x: int, y: int) -> None:
        self._open_curve.add_point(x, y)
        self._preview.add_point(x, y)

    def reset(self) -> None:
        self._open_curve.reset()
        self._preview.reset()

    @property
    def points(self) -> vtkPoints:
        return self._open_curve.points

    def get_props(self) -> list[vtkProp]:
        return [*self._open_curve.get_props(), *self._preview.get_props()]


class SegmentationScissorsWidget:
    """
    On slice view project 2D points on slice (world pos)
    On 3D view project 2D points on focal plane (world pos)
    """

    interaction_stopped = Signal(vtkPoints)

    def __init__(self) -> None:
        self._modifier: SegmentModifier | None = None
        self._view_node: vtkMRMLAbstractViewNode | None = None
        self._renderer: vtkRenderer | None = None
        self._brush = ScissorsPolygonBrush()
        self._brush_enabled = False
        self._painting = False

    def set_view_node(self, view_node):
        self._view_node = view_node

    def set_modifier(self, modifier: SegmentModifier):
        self._modifier = modifier

    def set_renderer(self, renderer):
        self.disable_brush()
        self._renderer = renderer

    def preview_point(self, x: int, y: int) -> None:
        self._brush.set_visible(True)
        self._brush.preview_point(x, y)

    def add_point(self, x: int, y: int) -> None:
        self._brush.add_point(x, y)

    def set_active(self, is_active: bool) -> None:
        if is_active:
            self.enable_brush()
        else:
            self.disable_brush()

    def enable_brush(self) -> None:
        if not self._renderer:
            return

        self._brush_enabled = True
        for prop in self._brush.get_props():
            self._renderer.AddViewProp(prop)

    def disable_brush(self) -> None:
        if not self._renderer:
            return

        if self.is_painting():
            self.stop_painting()
        self._brush.set_visible(False)
        self._brush_enabled = False
        for prop in self._brush.get_props():
            self._renderer.RemoveViewProp(prop)

    def is_brush_enabled(self) -> bool:
        return self._brush_enabled

    def start_painting(self, x: int, y: int) -> None:
        self._painting = True
        self.add_point(x, y)

    def stop_painting(self) -> None:
        self._painting = False
        # Reset brush before emitting signal to ensure reset is done
        points = vtkPoints()
        points.DeepCopy(self._brush.points)
        self._brush.reset()
        self.interaction_stopped.emit(points)

    def is_painting(self) -> bool:
        return self._painting


class SegmentationScissorsPipeline(SegmentationEffectPipeline[SegmentationEffectScissors]):
    def __init__(self) -> None:
        super().__init__()

        self.widget = SegmentationScissorsWidget()

        # Events we may consume and how we consume them
        self._supported_events: dict[int, Callable] = {
            int(vtkCommand.MouseMoveEvent): self._MouseMoved,
            int(vtkCommand.LeftButtonPressEvent): self._LeftButtonPressed,
            int(vtkCommand.LeftButtonReleaseEvent): self._LeftButtonReleased,
            int(vtkCommand.RightButtonPressEvent): self._RightButtonPressed,
        }

    @property
    def brush_interaction_mode(self) -> BrushInteractionMode:
        return self._effect.brush_interaction_mode

    def SetActive(self, isActive: bool):
        super().SetActive(isActive)
        self.widget.interaction_stopped.connect(self._OnWidgetInteractionStopped)
        self.widget.set_modifier(self._effect.modifier)
        self.widget.set_active(is_active=isActive)

    def _OnWidgetInteractionStopped(self, points: vtkPoints) -> None:
        if points.GetNumberOfPoints() == 0:
            return
        self._effect.apply_points_display_coordinates(points, self._view)

    def OnRendererAdded(self, renderer: vtkRenderer | None) -> None:
        self.widget.set_renderer(renderer)

    def OnRendererRemoved(self, _renderer: vtkRenderer) -> None:
        self.widget.set_renderer(None)

    def SetViewNode(self, viewNode: vtkMRMLAbstractViewNode) -> None:
        super().SetViewNode(viewNode)
        self.widget.set_view_node(viewNode)

    def SetDisplayNode(self, displayNode: vtkMRMLNode) -> None:
        super().SetDisplayNode(displayNode)

    def CanProcessInteractionEvent(self, eventData: vtkMRMLInteractionEventData) -> tuple[bool, float]:
        can_process = self.IsActive() and self.IsSupportedEvent(eventData)
        return can_process, 0.0

    def ProcessInteractionEvent(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if event_data.GetType() not in self._supported_events:
            return False

        callback = self._supported_events.get(event_data.GetType())
        return callback(event_data) if callback is not None else False

    def _LeftButtonPressed(self, event_data: vtkMRMLInteractionEventData) -> bool:
        x, y = event_data.GetDisplayPosition()
        if self.brush_interaction_mode == BrushInteractionMode.CONTINUOUS:
            self.widget.start_painting(x, y)
        elif self.brush_interaction_mode == BrushInteractionMode.POINT_BY_POINT:
            if not self.widget.is_painting():
                self.widget.start_painting(x, y)
            else:
                self.widget.add_point(x, y)
            self.widget.preview_point(x, y)
        self.RequestRender()
        return True

    def _LeftButtonReleased(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        if self.brush_interaction_mode == BrushInteractionMode.CONTINUOUS:
            self.widget.stop_painting()
            self.RequestRender()
            return True
        return False

    def _MouseMoved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        x, y = event_data.GetDisplayPosition()
        if self.widget.is_painting() and self.brush_interaction_mode == BrushInteractionMode.CONTINUOUS:
            self.widget.add_point(x, y)
        self.widget.preview_point(x, y)
        self.RequestRender()

        # Always let other interactor and displayable managers do whatever they want
        return False

    def _RightButtonPressed(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        if self.brush_interaction_mode == BrushInteractionMode.POINT_BY_POINT:
            self.widget.stop_painting()
            self.RequestRender()
            return True
        return False

    def IsSupportedEvent(self, event_data: vtkMRMLInteractionEventData):
        return event_data.GetType() in self._supported_events
