from __future__ import annotations

import math
from collections.abc import Callable

from slicer import vtkMRMLInteractionEventData
from vtkmodules.vtkCommonCore import reference as vtk_ref
from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkCommonExecutionModel import vtkAlgorithmOutput
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkGlyph3DMapper,
    vtkPolyDataMapper,
    vtkProp,
    vtkProperty,
)

from trame_slicer.views.threed_view import ThreeDView

from .segment_modifier import SegmentModifier
from .segment_paint_widget import (
    AbstractBrush,
    BrushModel,
    BrushShape,
    SegmentPaintWidget,
    SegmentPaintWidgetInteractor,
)


class Brush3D(AbstractBrush):
    def __init__(self):
        self.brush_mapper = vtkPolyDataMapper()
        self.brush_actor = vtkActor()
        self.brush_actor.SetMapper(self.brush_mapper)
        self.brush_actor.VisibilityOff()
        self.brush_actor.PickableOff()  # otherwise picking in 3D view would not work

    def set_input_connection(self, input_conn: vtkAlgorithmOutput):
        """
        Specify input polydata to use as brush
        """
        self.brush_mapper.SetInputConnection(input_conn)

    def get_prop(self) -> vtkProp:
        """
        Return brush prop.
        Can be used to add or remove the brush from the renderer, configure rendering properties (visibility, color, ...)
        """
        return self.brush_actor

    def get_property(self) -> vtkProperty:
        return self.brush_actor.GetProperty()


class BrushFeedback3D(AbstractBrush):
    """
    Uses a vtkGlyph3DMapper instead of a vtkGlyph3D + vtkPolyDataMapper
    More efficient than 3D Slicer implementation.
    """

    def __init__(self):
        self.brush_mapper = vtkGlyph3DMapper()
        self.brush_actor = vtkActor()
        self.brush_actor.SetMapper(self.brush_mapper)
        self.brush_actor.VisibilityOff()
        self.brush_actor.PickableOff()  # otherwise picking in 3D view would not work

    def set_source_connection(self, input_conn: vtkAlgorithmOutput):
        """
        Specify input polydata to use as brush
        """
        self.brush_mapper.SetSourceConnection(input_conn)

    # Specify input polydata to use as brush
    def set_input_data(self, input_conn: vtkPolyData):
        self.brush_mapper.SetInputData(input_conn)

    def get_prop(self) -> vtkProp:
        """
        Return brush prop.
        Can be used to add or remove the brush from the renderer, configure rendering properties (visibility, color, ...)
        """
        return self.brush_actor

    def get_property(self) -> vtkProperty:
        return self.brush_actor.GetProperty()


class SegmentPaintWidget3D(SegmentPaintWidget):
    def __init__(self, view: ThreeDView, modifier: SegmentModifier, brush_model: BrushModel):
        # brush
        brush = Brush3D()
        brush.set_input_connection(brush_model.get_output_port())
        brush.get_property().SetColor(1.0, 1.0, 0.2)

        # Feedback
        feedback_points_poly_data = vtkPolyData()

        # Feedback brush
        brush_feedback = BrushFeedback3D()
        brush_feedback.set_source_connection(brush_model.get_untransformed_output_port())
        brush_feedback.set_input_data(feedback_points_poly_data)
        brush_feedback.get_property().SetColor(1.0, 0.7, 0.0)

        super().__init__(view, modifier, brush_model, brush, brush_feedback)
        self._view = view  # for real type hint
        feedback_points_poly_data.SetPoints(self.paint_coordinates_world)

        self._last_position: tuple[float, float, float] | None = None
        self.enable_brush()  # enabled by default

    @property
    def view(self) -> ThreeDView:
        return self._view

    def absolute_brush_diameter(self) -> float:
        screenSizePixel = self._view.render_window().GetScreenSize()[1]
        renderer = self._view.renderer()
        # Viewport: xmin, ymin, xmax, ymax; range: 0.0-1.0; origin is bottom left
        # Determine the available renderer size in pixels
        minX = vtk_ref(0.0)
        minY = vtk_ref(0.0)
        renderer.NormalizedDisplayToDisplay(minX, minY)
        maxX = vtk_ref(1.0)
        maxY = vtk_ref(1.0)
        renderer.NormalizedDisplayToDisplay(maxX, maxY)
        rendererSizeInPixels = (
            int(maxX.get() - minX.get()),
            int(maxY.get() - minY.get()),
        )
        cam = renderer.GetActiveCamera()
        if cam.GetParallelProjection():
            # Parallel scale: height of the viewport in world-coordinate distances.
            # Larger numbers produce smaller images.
            mmPerPixel = (cam.GetParallelScale() * 2.0) / float(rendererSizeInPixels[1])
        else:
            tmp = cam.GetFocalPoint()
            cameraFP = (tmp[0], tmp[1], tmp[2], 1.0)
            cameraViewUp = cam.GetViewUp()

            # Get distance in pixels between two points at unit distance above and below the focal point
            renderer.SetWorldPoint(
                cameraFP[0] + cameraViewUp[0],
                cameraFP[1] + cameraViewUp[1],
                cameraFP[2] + cameraViewUp[2],
                cameraFP[3],
            )
            renderer.WorldToDisplay()
            topCenter = renderer.GetDisplayPoint()
            renderer.SetWorldPoint(
                cameraFP[0] - cameraViewUp[0],
                cameraFP[1] - cameraViewUp[1],
                cameraFP[2] - cameraViewUp[2],
                cameraFP[3],
            )
            renderer.WorldToDisplay()
            bottomCenter = renderer.GetDisplayPoint()
            distInPixels = math.dist(topCenter, bottomCenter)

            # 2.0 = 2x length of viewUp vector in mm (because viewUp is unit vector)
            mmPerPixel = 2.0 / distInPixels

        brushRelativeDiameter = 3.0
        return screenSizePixel * (brushRelativeDiameter / 100.0) * mmPerPixel

    def invalidate_world_position(self) -> None:
        self._last_position = None

    def update_world_position(self, position: list[float]) -> None:
        if not self.is_brush_enabled():
            return

        if self.is_painting():
            if self._last_position:
                self._interpolated_brush_position_if_needed(position)

            self.add_point_to_selection(position)

        self._brush_model.set_shape(BrushShape.Sphere)
        self._brush_model.world_origin_to_world_transform.Identity()
        self._brush_model.world_origin_to_world_transform.Translate(position)
        self._last_position = position

    def _interpolated_brush_position_if_needed(self, position):
        assert self._last_position is not None

        stroke_length = math.dist(position, self._last_position)
        maximum_distance_between_points = 0.2 * self.absolute_brush_diameter()
        if maximum_distance_between_points <= 0.0:
            return

        n_points_to_add = int(stroke_length / maximum_distance_between_points) - 1
        for i_pt in range(n_points_to_add):
            weight = float(i_pt + 1) / float(n_points_to_add + 1)

            weighted_point = [weight * self._last_position[i] + (1.0 - weight) * position[i] for i in range(3)]
            self.add_point_to_selection(weighted_point)


class SegmentPaintWidget3DInteractor(SegmentPaintWidgetInteractor):
    def __init__(self, widget: SegmentPaintWidget3D) -> None:
        super().__init__(widget)
        self._widget = widget  # for type hints
        self._render_callback: Callable | None = None

        # Events we may consume and how we consume them
        self._supported_events: dict[int, Callable] = {
            int(vtkCommand.MouseMoveEvent): self.mouse_moved,
            int(vtkCommand.LeftButtonPressEvent): self.left_pressed,
            int(vtkCommand.LeftButtonReleaseEvent): self.left_released,
        }

    @property
    def widget(self) -> SegmentPaintWidget3D:
        return self._widget

    @property
    def is_brush_enabled(self):
        return self.widget.is_brush_enabled()

    @property
    def has_pick_hit(self):
        return self.widget.view.has_pick_hit()

    def process_event(self, event_data: vtkMRMLInteractionEventData) -> bool:
        is_not_supported_event = event_data.GetType() not in self._supported_events
        if not self.is_brush_enabled or is_not_supported_event:
            return False

        callback = self._supported_events[event_data.GetType()]
        return callback(event_data)

    def left_pressed(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if not self.is_brush_enabled or not self.has_pick_hit:
            return False

        self.widget.start_painting()
        self.widget.add_point_to_selection(event_data.GetWorldPosition())
        self.widget.view.schedule_render()
        self.trigger_render_callback()
        return True

    def left_released(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_painting():
            self.widget.stop_painting()
            self.widget.view.schedule_render()
            self.trigger_render_callback()

        # Always let other interactor and displayable managers do whatever they want
        return False

    def mouse_moved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if self.is_brush_enabled and self.has_pick_hit:
            self.widget.update_world_position(event_data.GetWorldPosition())
            self.widget.view.schedule_render()
            self.trigger_render_callback()
        else:
            self.widget.invalidate_world_position()

        # Always let other interactor and displayable managers do whatever they want
        return False
