from __future__ import annotations

from collections.abc import Callable

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLInteractionEventData,
    vtkMRMLNode,
    vtkMRMLSliceNode,
)
from vtkmodules.vtkCommonCore import vtkCommand, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkQuad
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkRenderingCore import (
    vtkActor2D,
    vtkCoordinate,
    vtkPolyDataMapper2D,
    vtkProp,
    vtkProperty2D,
    vtkRenderer,
)

from .segment_modifier import SegmentModifier
from .segmentation_effect_pipeline import SegmentationEffectPipeline


class ScissorsPolygonBrush:
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


class SegmentationScissorsWidget:
    """
    On slice view project 2D points on slice (world pos)
    On 3D view project 2D points on focal plane (world pos)
    """

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

    def move_last_point(self, x: int, y: int) -> None:
        self._brush.move_last_point(x, y)

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

        self._brush.set_visibility(True)
        self._brush_enabled = True
        self._renderer.AddViewProp(self._brush.get_prop())

    def disable_brush(self) -> None:
        if not self._renderer:
            return

        if self.is_painting():
            self.stop_painting()
        self._brush.set_visibility(False)
        self._brush_enabled = False
        self._renderer.RemoveViewProp(self._brush.get_prop())

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
        if isinstance(self._view_node, vtkMRMLSliceNode):
            return self._display_to_world_slice(display_coords, self._view_node)
        return self._display_to_world_generic(display_coords, dc_to_wc)

    def _display_to_world_slice(
        self, display_coords: list[float], slice_node: vtkMRMLSliceNode
    ) -> tuple[list[float], list[float]]:
        xy_to_slice: vtkMatrix4x4 = slice_node.GetXYToRAS()

        max_dim = max(self._modifier.volume_node.GetImageData().GetBounds())

        near = xy_to_slice.MultiplyPoint([display_coords[0], display_coords[1], -max_dim, 1.0])
        far = xy_to_slice.MultiplyPoint([display_coords[0], display_coords[1], max_dim, 1.0])

        return list(near), list(far)

    def _display_to_world_generic(
        self, display_coords: list[float], dc_to_wc: vtkCoordinate
    ) -> tuple[list[float], list[float]]:
        renderer = self._renderer

        dc_to_wc.SetValue(display_coords[0], display_coords[1], 0.0)
        near = dc_to_wc.GetComputedWorldValue(renderer)

        dc_to_wc.SetValue(display_coords[0], display_coords[1], 1.0)
        far = dc_to_wc.GetComputedWorldValue(renderer)

        return list(near), list(far)


class SegmentationScissorsPipeline(SegmentationEffectPipeline):
    def __init__(self) -> None:
        super().__init__()

        self.widget = SegmentationScissorsWidget()

        # Events we may consume and how we consume them
        self._supported_events: dict[int, Callable] = {
            int(vtkCommand.MouseMoveEvent): self._MouseMoved,
            int(vtkCommand.LeftButtonPressEvent): self._LeftButtonPressed,
            int(vtkCommand.LeftButtonReleaseEvent): self._LeftButtonReleased,
        }

    def SetActive(self, isActive: bool):
        super().SetActive(isActive)
        self.widget.set_modifier(self._effect.modifier)
        self.widget.set_active(is_active=isActive)

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
        self.widget.start_painting(x, y)
        self.RequestRender()
        return True

    def _LeftButtonReleased(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        self.widget.stop_painting()
        self.RequestRender()
        return True

    def _MouseMoved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        x, y = event_data.GetDisplayPosition()
        self.widget.move_last_point(x, y)
        if self.widget.is_painting():
            self.widget.add_point(x, y)
        self.RequestRender()

        # Always let other interactor and displayable managers do whatever they want
        return False

    def IsSupportedEvent(self, event_data: vtkMRMLInteractionEventData):
        return event_data.GetType() in self._supported_events
