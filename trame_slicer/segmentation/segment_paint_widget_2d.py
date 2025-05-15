from __future__ import annotations

import math
from collections.abc import Callable
from enum import Enum, auto

from slicer import vtkMRMLInteractionEventData
from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkCommonDataModel import vtkPlane, vtkPolyData
from vtkmodules.vtkCommonExecutionModel import vtkAlgorithmOutput
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkCutter, vtkGlyph3D
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkRenderingCore import (
    vtkActor2D,
    vtkPolyDataMapper2D,
    vtkProp,
    vtkProperty2D,
)

from trame_slicer.views.slice_view import SliceView

from .segment_modifier import SegmentModifier
from .segment_paint_widget import (
    AbstractBrush,
    BrushModel,
    BrushShape,
    SegmentPaintWidget,
    SegmentPaintWidgetInteractor,
)


class Brush2D(AbstractBrush):
    """
    Display a vtkPolyData on a Slice
    This takes a vtkPolyData(Algorithm output port) as input and expect it to be pre transformed in world position
    """

    def __init__(self):
        super().__init__()

        self._slice_plane = vtkPlane()

        self._brush_cutter = vtkCutter()
        self._brush_cutter.SetCutFunction(self._slice_plane)
        self._brush_cutter.SetGenerateCutScalars(0)

        self._world_to_slice_transform = vtkTransform()
        self._brush_world_to_slice_transformer = vtkTransformPolyDataFilter()
        self._brush_world_to_slice_transformer.SetTransform(self._world_to_slice_transform)
        self._brush_world_to_slice_transformer.SetInputConnection(self._brush_cutter.GetOutputPort())

        self._brush_mapper = vtkPolyDataMapper2D()
        self._brush_mapper.SetInputConnection(self._brush_world_to_slice_transformer.GetOutputPort())
        self._brush_actor = vtkActor2D()
        self._brush_actor.SetMapper(self._brush_mapper)
        self._brush_actor.VisibilityOff()

    # Specify input polydata to use as brush
    def set_input_connection(self, input_conn: vtkAlgorithmOutput):
        self._brush_cutter.SetInputConnection(input_conn)

    def get_prop(self) -> vtkProp:
        """
        Return brush prop.
        Can be used to add or remove the brush from the renderer, configure rendering properties (visibility, color, ...)
        """
        return self._brush_actor

    def get_property(self) -> vtkProperty2D:
        return self._brush_actor.GetProperty()

    def update_slice_position(self, xy_to_ras: vtkMatrix4x4):
        """
        Set current slice XY to RAS matrix.
        This should be called every time the current slice changes in the slice node
        """
        self._slice_plane.SetNormal(
            xy_to_ras.GetElement(0, 2),
            xy_to_ras.GetElement(1, 2),
            xy_to_ras.GetElement(2, 2),
        )
        self._slice_plane.SetOrigin(
            xy_to_ras.GetElement(0, 3),
            xy_to_ras.GetElement(1, 3),
            xy_to_ras.GetElement(2, 3),
        )

        ras_to_xy = vtkMatrix4x4()
        vtkMatrix4x4.Invert(xy_to_ras, ras_to_xy)
        self._world_to_slice_transform.SetMatrix(ras_to_xy)


class BrushScaleMode(Enum):
    Absolute = auto()
    ScreenInvariant = auto()


class SegmentPaintWidget2D(SegmentPaintWidget):
    def __init__(self, view: SliceView, modifier: SegmentModifier, brush_model: BrushModel):
        # brush
        brush = Brush2D()
        brush.set_input_connection(brush_model.get_output_port())
        brush.get_property().SetColor(1.0, 1.0, 0.2)

        # Feedback brush
        feedback_points_poly_data = vtkPolyData()
        feedback_glyph_filter = vtkGlyph3D()
        feedback_glyph_filter.SetInputData(feedback_points_poly_data)
        feedback_glyph_filter.SetSourceConnection(brush_model.get_untransformed_output_port())
        brush_feedback = Brush2D()
        brush_feedback.set_input_connection(feedback_glyph_filter.GetOutputPort())
        brush_feedback.get_property().SetColor(0.7, 0.7, 0.0)
        brush_feedback.get_property().SetOpacity(0.5)

        # Setup parent
        super().__init__(view, modifier, brush_model, brush, brush_feedback)
        self._brush_scale_mode = BrushScaleMode.ScreenInvariant
        self._view = view  # for type hints
        self._brush = brush
        self._brush_feedback = brush_feedback
        relative_brush_size = 5
        self._brush_diameter_pix = (relative_brush_size / 100) * self._vertical_screen_size()

        feedback_points_poly_data.SetPoints(self.paint_coordinates_world)
        self.view.mrml_view_node.AddObserver(vtkCommand.ModifiedEvent, self._on_slice_changed, -1.0)

        self._on_slice_changed(None, None)
        self.enable_brush()

    def enable_brush(self) -> None:
        super().enable_brush()
        self.update_brush_diameter()

    @property
    def view(self) -> SliceView:
        return self._view

    @property
    def brush_diameter_pix(self):
        if self._brush_scale_mode == BrushScaleMode.ScreenInvariant:
            return self._brush_diameter_pix

        return self._compute_brush_pixel_diameter_from_absolute(self._brush_diameter_pix)

    def _get_mm_per_pixel(self):
        xy_to_slice: vtkMatrix4x4 = self.view.mrml_view_node.GetXYToSlice()
        return math.sqrt(sum([xy_to_slice.GetElement(i, 1) ** 2 for i in range(3)]))

    def _compute_brush_pixel_diameter_from_absolute(self, brush_diameter_mm):
        mm_per_pixel = self._get_mm_per_pixel()
        if mm_per_pixel == 0:
            return brush_diameter_mm

        return brush_diameter_mm / mm_per_pixel

    def _vertical_screen_size(self):
        return self.view.render_window().GetScreenSize()[1]

    def update_brush_diameter(self) -> None:
        self._brush_model.set_cylinder_parameters(
            radius=self.brush_diameter_pix / 2.0,
            resolution=32,
            height=self.view.get_slice_step() / 2.0,
        )

    def update_mouse_position(self, position: tuple[int, int]) -> None:
        if not self.is_brush_enabled():
            return

        self.update_brush_diameter()
        xy_to_ras: vtkMatrix4x4 = self.view.mrml_view_node.GetXYToRAS()
        world_pos = list(xy_to_ras.MultiplyPoint((float(position[0]), float(position[1]), 0.0, 1.0)))
        self._update_brush_position(world_pos[0:3], xy_to_ras)
        if self.is_painting():
            self.add_point_to_selection(world_pos[:3])

    def _update_brush_position(self, world_pos: list[float], xy_to_ras: vtkMatrix4x4) -> None:
        self._brush_model.set_shape(BrushShape.Cylinder)

        # brush is rotated to the slice widget plane
        brush_to_world_origin_transform_matrix = vtkMatrix4x4()
        brush_to_world_origin_transform_matrix.DeepCopy(xy_to_ras)
        brush_to_world_origin_transform_matrix.SetElement(0, 3, 0)
        brush_to_world_origin_transform_matrix.SetElement(1, 3, 0)
        brush_to_world_origin_transform_matrix.SetElement(2, 3, 0)

        # cylinder's long axis is the Y axis, we need to rotate it to Z axis
        self._brush_model.brush_to_world_origin_transform.Identity()
        self._brush_model.brush_to_world_origin_transform.Concatenate(brush_to_world_origin_transform_matrix)
        self._brush_model.brush_to_world_origin_transform.RotateX(90)

        self._brush_model.world_origin_to_world_transform.Identity()
        self._brush_model.world_origin_to_world_transform.Translate(world_pos[:3])

    def _on_slice_changed(self, _caller, _ev) -> None:
        self._brush.update_slice_position(self.view.mrml_view_node.GetXYToRAS())
        self._brush_feedback.update_slice_position(self.view.mrml_view_node.GetXYToRAS())
        self.update_brush_diameter()


class SegmentPaintWidget2DInteractor(SegmentPaintWidgetInteractor):
    def __init__(self, widget: SegmentPaintWidget2D) -> None:
        super().__init__(widget)
        self._widget = widget  # for type hints

        # Events we may consume and how we consume them
        self._supported_events: dict[int, Callable] = {
            int(vtkCommand.MouseMoveEvent): self.mouse_moved,
            int(vtkCommand.LeftButtonPressEvent): self.left_pressed,
            int(vtkCommand.LeftButtonReleaseEvent): self.left_released,
        }

    @property
    def widget(self) -> SegmentPaintWidget2D:
        return self._widget

    def process_event(self, event_data: vtkMRMLInteractionEventData) -> bool:
        is_not_supported_event = event_data.GetType() not in self._supported_events
        if not self.widget.is_brush_enabled() or is_not_supported_event:
            return False

        callback = self._supported_events.get(event_data.GetType())
        return callback(event_data) if callback is not None else False

    def left_pressed(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_brush_enabled():
            self.widget.start_painting()
            self._paint_at_event_position(event_data)
            return True

        return False

    def left_released(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_painting():
            self.widget.stop_painting()

        # Always let other interactor and displayable managers do whatever they want
        return False

    def mouse_moved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        if self.widget.is_brush_enabled():
            self._paint_at_event_position(event_data)

        # Always let other interactor and displayable managers do whatever they want
        return False

    def _paint_at_event_position(self, event_data: vtkMRMLInteractionEventData):
        self.widget.update_mouse_position(event_data.GetDisplayPosition())
        self.widget.view.schedule_render()
        self.trigger_render_callback()
