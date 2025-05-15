from __future__ import annotations

from collections.abc import Callable

from slicer import vtkMRMLInteractionEventData
from vtkmodules.vtkCommonCore import vtkCommand, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkQuad
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkRenderingCore import (
    vtkActor2D,
    vtkCoordinate,
    vtkPolyDataMapper2D,
    vtkProp,
    vtkProperty2D,
)

from trame_slicer.views import AbstractView, AbstractViewInteractor, SliceView

from .segment_modifier import SegmentModifier
from .segmentation_widget import SegmentationWidget


class ScissorPolygonBrush:
    """Display the scissors as 2D lines"""

    def __init__(self):
        super().__init__()
        self._points = vtkPoints()
        self._lines = vtkCellArray()
        self._vertices = vtkCellArray()
        self._poly = vtkPolyData()
        self._poly.SetLines(self._lines)
        self._poly.SetVerts(self._vertices)
        self._poly.SetPoints(self._points)

        self._brush_mapper = vtkPolyDataMapper2D()
        self._brush_mapper.SetInputData(self._poly)
        self._brush_actor = vtkActor2D()
        self._brush_actor.SetMapper(self._brush_mapper)
        self._brush_actor.VisibilityOff()
        props = self._brush_actor.GetProperty()
        props.SetColor(1.0, 1.0, 0.0)
        props.SetPointSize(4.0)
        props.SetLineWidth(2.0)

    def set_visibility(self, visible: bool):
        self._brush_actor.SetVisibility(int(visible))

    def move_last_point(self, x: int, y: int) -> None:
        count = self._points.GetNumberOfPoints()
        if count == 0:
            self.add_point(x, y)
        else:
            self._points.SetPoint(count - 1, [float(x), float(y), 1.0])
            self._points.Modified()

    def add_point(self, x: int, y: int) -> None:
        self._points.InsertNextPoint([float(x), float(y), 1.0])
        count = self._points.GetNumberOfPoints()
        if count > 1:
            self._lines.InsertNextCell(2, [count - 1, count - 2])
        self._vertices.InsertNextCell(1, [count - 1])

    def reset(self) -> None:
        self._points.SetNumberOfPoints(0)
        self._lines.Reset()
        self._vertices.Reset()
        self._poly.Modified()

    @property
    def points(self) -> vtkPoints:
        return self._points

    def get_prop(self) -> vtkProp:
        """
        Return brush prop.
        Can be used to add or remove the brush from the renderer, configure rendering properties (visibility, color, ...)
        """
        return self._brush_actor

    def get_property(self) -> vtkProperty2D:
        return self._brush_actor.GetProperty()


class SegmentScissorWidget(SegmentationWidget):
    """
    On slice view project 2D points on slice (world pos)
    On 3D view project 2D points on focal plane (world pos)
    """

    def __init__(self, view: AbstractView, modifier: SegmentModifier) -> None:
        super().__init__(modifier)
        self._view = view
        self._brush = ScissorPolygonBrush()
        self._brush_enabled = False
        self._painting = False

    def move_last_point(self, x: int, y: int) -> None:
        self._brush.move_last_point(x, y)

    def add_point(self, x: int, y: int) -> None:
        self._brush.add_point(x, y)

    def enable_brush(self) -> None:
        self._brush.set_visibility(True)
        self._brush_enabled = True
        renderer = self._view.renderer()
        renderer.AddViewProp(self._brush.get_prop())

    def disable_brush(self) -> None:
        if self.is_painting():
            self.stop_painting()
        self._brush.set_visibility(False)
        self._brush_enabled = False
        renderer = self._view.renderer()
        renderer.RemoveViewProp(self._brush.get_prop())

    def is_brush_enabled(self) -> bool:
        return self._brush_enabled

    def start_painting(self, x: int, y: int) -> None:
        self._painting = True
        self.add_point(x, y)

    def stop_painting(self) -> None:
        self._painting = False
        self.commit()
        self._brush.reset()

    def is_painting(self) -> bool:
        return self._painting

    def commit(self):
        # need at least 3 points to create a closed polydata
        if self._brush.points.GetNumberOfPoints() >= 3:
            self._modifier.apply_polydata_world(self._create_poly())

    def _create_poly(self) -> vtkPolyData:
        # DisplayToWorldCoordinate
        nodes = self._brush.points
        point_count = nodes.GetNumberOfPoints()

        polydata = vtkPolyData()
        points = vtkPoints()
        points.SetNumberOfPoints(2 * point_count)
        polydata.SetPoints(points)
        cells = vtkCellArray()
        polydata.SetPolys(cells)

        quad = vtkQuad()
        ids = quad.GetPointIds()
        ids.SetNumberOfIds(4)

        dc_to_wc = vtkCoordinate()
        dc_to_wc.SetCoordinateSystemToDisplay()

        for i in range(point_count):
            node_position_dc = [0.0, 0.0, 0.0]
            nodes.GetPoint(i, node_position_dc)

            near, far = self._display_to_world(node_position_dc, dc_to_wc)

            points.SetPoint(2 * i, near[:3])
            points.SetPoint(2 * i + 1, far[:3])

            ids.SetId(0, 2 * i)
            ids.SetId(1, 2 * i + 1)
            ids.SetId(2, (2 * i + 3) % (2 * point_count))
            ids.SetId(3, (2 * i + 2) % (2 * point_count))
            cells.InsertNextCell(quad)

        return polydata

    def _display_to_world(
        self, display_coords: list[float], dc_to_wc: vtkCoordinate
    ) -> tuple[list[float], list[float]]:
        if isinstance(self._view, SliceView):
            return self._display_to_world_slice(display_coords, self._view)
        return self._display_to_world_generic(display_coords, dc_to_wc)

    def _display_to_world_slice(self, display_coords: list[float], view: SliceView) -> tuple[list[float], list[float]]:
        xy_to_slice: vtkMatrix4x4 = view.logic.GetSliceNode().GetXYToRAS()

        max_dim = max(self.modifier.volume_node.GetImageData().GetBounds())

        near = xy_to_slice.MultiplyPoint([display_coords[0], display_coords[1], -max_dim, 1.0])
        far = xy_to_slice.MultiplyPoint([display_coords[0], display_coords[1], max_dim, 1.0])

        return list(near), list(far)

    def _display_to_world_generic(
        self, display_coords: list[float], dc_to_wc: vtkCoordinate
    ) -> tuple[list[float], list[float]]:
        renderer = self._view.renderer()

        dc_to_wc.SetValue(display_coords[0], display_coords[1], 0.0)
        near = dc_to_wc.GetComputedWorldValue(renderer)

        dc_to_wc.SetValue(display_coords[0], display_coords[1], 1.0)
        far = dc_to_wc.GetComputedWorldValue(renderer)

        return list(near), list(far)


class SegmentScissorWidgetInteractor(AbstractViewInteractor):
    def __init__(self, widget: SegmentScissorWidget) -> None:
        super().__init__()
        self._widget = widget  # for type hints
        self._render_callback: Callable | None = None

        # Events we may consume and how we consume them
        self._supported_events: dict[int, Callable] = {
            int(vtkCommand.MouseMoveEvent): self.mouse_moved,
            int(vtkCommand.LeftButtonPressEvent): self.left_pressed,
            int(vtkCommand.LeftButtonReleaseEvent): self.left_released,
        }

    @property
    def widget(self) -> SegmentScissorWidget:
        return self._widget

    def process_event(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if event_data.GetType() not in self._supported_events:
            return False

        callback = self._supported_events.get(event_data.GetType())
        return callback(event_data) if callback is not None else False

    def left_pressed(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if not self._widget.is_brush_enabled():
            return False

        x, y = event_data.GetDisplayPosition()
        self.widget.start_painting(x, y)
        self.trigger_render_callback()
        return True

    def left_released(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        if not self.widget.is_painting():
            return False

        self.widget.stop_painting()
        self.trigger_render_callback()
        return True

    def mouse_moved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if self._widget.is_brush_enabled():
            x, y = event_data.GetDisplayPosition()
            self.widget.move_last_point(x, y)
            if self._widget.is_painting():
                self.widget.add_point(x, y)
            self.trigger_render_callback()

        # Always let other interactor and displayable managers do whatever they want
        return False
