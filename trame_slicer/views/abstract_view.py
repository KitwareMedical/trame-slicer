from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal, TypeVar

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLDisplayableManagerGroup,
    vtkMRMLScene,
    vtkMRMLViewNode,
)
from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkRenderingCore import (
    vtkInteractorStyle,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from trame_slicer.utils import VtkEventDispatcher

from .abstract_view_interactor import AbstractViewInteractor
from .render_scheduler import DirectRendering, ScheduledRenderStrategy
from .view_interaction_dispatch import (
    ViewInteractionDispatch,
    ViewInteractionDispatchChild,
)

ViewOrientation = Literal["Axial", "Coronal", "Sagittal"]


@dataclass
class ViewProps:
    label: str | None = None
    orientation: ViewOrientation | None = None
    color: str | None = None
    group: int | None = None
    background_color: str | tuple[str, str] | None = None
    box_visible: bool | None = None

    def __post_init__(self):
        if self.group is not None:
            self.group = int(self.group)

    def to_xml(self) -> str:
        property_map = {key: getattr(self, value) for key, value in self.xml_name_map().items()}

        return "".join(
            f'<property name="{name}" action="default">{value}</property>'
            for name, value in property_map.items()
            if value is not None
        )

    @classmethod
    def xml_name_map(cls):
        return {
            "orientation": "orientation",
            "viewlabel": "label",
            "viewcolor": "color",
            "viewgroup": "group",
            "background_color": "background_color",
            "box_visible": "box_visible",
        }

    @classmethod
    def from_xml_dict(cls, xml_prop_dict: dict):
        name_map = cls.xml_name_map()
        renamed_dict = {name_map[key]: value for key, value in xml_prop_dict.items()}
        return cls(**renamed_dict)


AbstractViewChild = TypeVar("AbstractViewChild", bound="AbstractView")


class AbstractView:
    """
    Simple container class for a VTK Render Window, Renderers and VTK MRML Displayable Manager Group
    """

    def __init__(
        self,
        scheduled_render_strategy: ScheduledRenderStrategy | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, *kwargs)
        self._renderer = vtkRenderer()
        self._render_window = vtkRenderWindow()
        self._render_window.ShowWindowOff()
        self._render_window.SetMultiSamples(0)
        self._render_window.AddRenderer(self._renderer)

        self._render_window_interactor = vtkRenderWindowInteractor()
        self._render_window_interactor.SetRenderWindow(self._render_window)
        self._render_window_interactor.Initialize()

        self.displayable_manager_group = vtkMRMLDisplayableManagerGroup()
        self.displayable_manager_group.SetRenderer(self._renderer)
        self.displayable_manager_group.AddObserver(vtkCommand.UpdateEvent, self.schedule_render)
        self.mrml_scene: vtkMRMLScene | None = None
        self.mrml_view_node: vtkMRMLAbstractViewNode | None = None

        self._scheduled_render: ScheduledRenderStrategy | None = None
        self.set_scheduled_render(scheduled_render_strategy or DirectRendering())
        self._view_properties = ViewProps()

        self._modified_dispatcher = VtkEventDispatcher()
        self._modified_dispatcher.set_dispatch_information(self)
        self._mrml_node_obs_id = None
        self._view_interaction_dispatch = self.create_interaction_dispatch()

    def create_interaction_dispatch(self) -> ViewInteractionDispatchChild:
        return ViewInteractionDispatch(self)

    def add_user_interactor(self, observer: AbstractViewInteractor):
        self._view_interaction_dispatch.add_user_interactor(observer)

    def remove_user_interactor(self, observer: AbstractViewInteractor):
        self._view_interaction_dispatch.remove_user_interactor(observer)

    def set_scheduled_render(self, scheduled_render_strategy: ScheduledRenderStrategy) -> None:
        self._scheduled_render = scheduled_render_strategy or DirectRendering()
        self._scheduled_render.set_abstract_view(self)

    def finalize(self):
        self.render_window().ShowWindowOff()
        self.render_window().Finalize()

    def add_renderer(self, renderer: vtkRenderer) -> None:
        self._render_window.AddRenderer(renderer)

    def renderers(self) -> list[vtkRenderer]:
        return list(self._render_window.GetRenderers())

    def first_renderer(self) -> vtkRenderer:
        return self._renderer

    def renderer(self) -> vtkRenderer:
        return self.first_renderer()

    def schedule_render(self, *_) -> None:
        if not self._scheduled_render:
            return
        self._scheduled_render.schedule_render()

    def render(self) -> None:
        self._render_window_interactor.Render()
        if not self._scheduled_render:
            return
        self._scheduled_render.did_render()

    def render_window(self) -> vtkRenderWindow:
        return self._render_window

    def interactor(self) -> vtkRenderWindowInteractor:
        return self.render_window().GetInteractor()

    def interactor_style(self) -> vtkInteractorStyle | None:
        return self.interactor().GetInteractorStyle()

    def set_mrml_view_node(self, node: vtkMRMLViewNode) -> None:
        if self.mrml_view_node == node:
            return

        with self.trigger_modified_once():
            self._modified_dispatcher.detach_vtk_observer(self._mrml_node_obs_id)
            self.mrml_view_node = node
            self.displayable_manager_group.SetMRMLDisplayableNode(node)
            self._reset_node_view_properties()
            self._mrml_node_obs_id = self._modified_dispatcher.attach_vtk_observer(node, "ModifiedEvent")

    def set_view_properties(self, view_properties: ViewProps):
        self._view_properties = view_properties
        self._reset_node_view_properties()

    def _reset_node_view_properties(self):
        if not self.mrml_view_node:
            return

        with self.trigger_modified_once():
            self._call_if_value_not_none(self.mrml_view_node.SetViewGroup, self._view_properties.group)
            self._call_if_value_not_none(
                self.set_background_color_from_string,
                self._view_properties.background_color,
            )

    def get_view_group(self) -> int:
        if not self.mrml_view_node:
            return 0
        return self.mrml_view_node.GetViewGroup()

    def get_singleton_tag(self) -> str:
        if not self.mrml_view_node:
            return ""
        return self.mrml_view_node.GetSingletonTag()

    @classmethod
    def _call_if_value_not_none(cls, setter, value):
        if value is not None:
            setter(value)

    def set_mrml_scene(self, scene: vtkMRMLScene) -> None:
        if self.mrml_scene == scene:
            return

        self.mrml_scene = scene
        if self.mrml_view_node and self.mrml_view_node.GetScene() != scene:
            self.mrml_view_node = None

    def reset_camera(self):
        for renderer in self._render_window.GetRenderers():
            renderer.ResetCamera()

    def add_modified_observer(self, observer: Callable) -> None:
        self._modified_dispatcher.add_dispatch_observer(observer)

    def remove_modified_observer(self, observer: Callable) -> None:
        self._modified_dispatcher.remove_dispatch_observer(observer)

    def get_view_node_id(self) -> str:
        return self.mrml_view_node.GetID() if self.mrml_view_node else ""

    def fit_view_to_content(self):
        self.reset_camera()

    def reset_view(self):
        with self.trigger_modified_once():
            self._reset_node_view_properties()
            self.fit_view_to_content()
            self.schedule_render()
            self._trigger_modified()

    def set_background_color(self, rgb_int_color: list[int]) -> None:
        self.set_background_gradient_color(rgb_int_color, rgb_int_color)

    def set_background_gradient_color(self, color1_rgb_int: list[int], color2_rgb_int: list[int]) -> None:
        self.first_renderer().SetBackground(*self._to_float_color(color1_rgb_int))
        self.first_renderer().SetBackground2(*self._to_float_color(color2_rgb_int))

    def set_background_color_from_string(self, color: str | tuple[str, str]):
        if isinstance(color, str):
            c1 = c2 = color
        else:
            c1, c2 = color
        self.set_background_gradient_color(self._str_to_color(c1), (self._str_to_color(c2)))

    @staticmethod
    def _to_float_color(rgb_int_color: list[int]) -> list[float]:
        return [int_color / 255.0 for int_color in rgb_int_color]

    @classmethod
    def _str_to_color(cls, color: str) -> list[int]:
        from webcolors import hex_to_rgb, name_to_rgb

        try:
            int_color = hex_to_rgb(color)
        except ValueError:
            int_color = name_to_rgb(color)
        return [int_color.red, int_color.green, int_color.blue]

    def _trigger_modified(self) -> None:
        self._modified_dispatcher.trigger_dispatch()

    @contextmanager
    def trigger_modified_once(self):
        prev_blocked = self._modified_dispatcher.is_blocked()
        self._modified_dispatcher.set_blocked(True)
        try:
            yield
        finally:
            self._modified_dispatcher.set_blocked(prev_blocked)
            self._trigger_modified()

    def set_orientation_marker(
        self,
        orientation_marker: int | None = None,
        orientation_marker_size: int | None = None,
    ):
        """
        Sets the orientation marker and size.
        Orientation Enums are defined in the vtkMRMLAbstractViewNode class.
        """
        if orientation_marker is not None:
            self.mrml_view_node.SetOrientationMarkerType(orientation_marker)

        if orientation_marker_size is not None:
            self.mrml_view_node.SetOrientationMarkerSize(orientation_marker_size)

    def set_ruler(self, ruler_type: int | None = None, ruler_color: int | None = None):
        """
        Sets the ruler type and color.
        Ruler Enums are defined in the vtkMRMLAbstractViewNode class.
        """
        if ruler_type is not None:
            self.mrml_view_node.SetRulerType(ruler_type)

        if ruler_color is not None:
            self.mrml_view_node.SetRulerColor(ruler_color)

    def start_interactor(self) -> None:
        self.interactor().Start()
