from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

from slicer import (
    vtkMRMLAbstractDisplayableManager,
    vtkMRMLAbstractViewNode,
    vtkMRMLApplicationLogic,
    vtkMRMLDisplayableManagerFactory,
    vtkMRMLDisplayableManagerGroup,
    vtkMRMLLayerDMObjectEventObserverScripted,
    vtkMRMLScene,
    vtkMRMLViewNode,
)
from undo_stack import Signal
from vtkmodules.vtkCommonCore import vtkCommand, vtkObject
from vtkmodules.vtkRenderingCore import (
    vtkInteractorObserver,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from .render_scheduler import DirectRendering, ScheduledRenderStrategy

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

    modified = Signal("AbstractView")

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
        self._render_window.SetMultiSamples(8)
        self._render_window.AddRenderer(self._renderer)

        self._render_window_interactor = vtkRenderWindowInteractor()
        self._render_window_interactor.SetRenderWindow(self._render_window)
        self._render_window_interactor.Initialize()

        self._displayable_manager_group = vtkMRMLDisplayableManagerGroup()
        self._displayable_manager_group.SetRenderer(self._renderer)
        self._displayable_manager_group.AddObserver(vtkCommand.UpdateEvent, self.schedule_render)
        self._scene: vtkMRMLScene | None = None
        self._view_node: vtkMRMLAbstractViewNode | None = None

        self._scheduled_render: ScheduledRenderStrategy | None = None
        self.set_scheduled_render(scheduled_render_strategy or DirectRendering())
        self._view_properties = ViewProps()

        self._event_observer = vtkMRMLLayerDMObjectEventObserverScripted()
        self._event_observer.SetPythonCallback(self._on_object_event)
        self._mrml_node_obs_id = None

        self._is_render_blocked = False

    def _initialize_displayable_manager_group(
        self,
        factory_type: vtkMRMLDisplayableManagerFactory,
        app_logic: vtkMRMLApplicationLogic,
        manager_types: list[type[vtkMRMLAbstractDisplayableManager] | str],
    ) -> None:
        """
        Initialize the displayable manager group with the given input factory type and the list of displayable managers.

        :param factory_type: vtkMRMLDisplayableManagerFactory responsible for the current view.
        :param app_logic: Slicer application logic.
        :param manager_types: List of displayable managers to register in view.
        """
        factory = factory_type.GetInstance()
        factory.SetMRMLApplicationLogic(app_logic)

        manager_names = [
            manager_type if isinstance(manager_type, str) else manager_type.__name__ for manager_type in manager_types
        ]
        for manager in manager_names:
            if not factory.IsDisplayableManagerRegistered(manager):
                factory.RegisterDisplayableManager(manager)

        self._displayable_manager_group.Initialize(factory, self.renderer())

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
        if not self._scheduled_render or self._is_render_blocked:
            return
        self._scheduled_render.schedule_render()

    def render(self) -> None:
        if self._is_render_blocked:
            return
        self._render_window_interactor.Render()
        if not self._scheduled_render:
            return
        self._scheduled_render.did_render()

    def render_window(self) -> vtkRenderWindow:
        return self._render_window

    def interactor(self) -> vtkRenderWindowInteractor:
        return self.render_window().GetInteractor()

    def interactor_style(self) -> vtkInteractorObserver | None:
        return self.interactor().GetInteractorStyle()

    def set_view_node(self, node: vtkMRMLViewNode) -> None:
        if self._view_node == node:
            return

        with self.trigger_modified_once():
            self._event_observer.UpdateObserver(self._view_node, node)
            self._view_node = node
            self._displayable_manager_group.SetMRMLDisplayableNode(node)
            self._reset_node_view_properties()

    def set_view_properties(self, view_properties: ViewProps):
        self._view_properties = view_properties
        self._reset_node_view_properties()

    def _reset_node_view_properties(self):
        if not self._view_node:
            return

        with self.trigger_modified_once():
            self._call_if_value_not_none(self._view_node.SetViewGroup, self._view_properties.group)
            self._call_if_value_not_none(
                self.set_background_color_from_string,
                self._view_properties.background_color,
            )
            self._call_if_value_not_none(self.set_layout_color_from_string, self._view_properties.color)

    def get_view_group(self) -> int:
        if not self._view_node:
            return 0
        return self._view_node.GetViewGroup()

    def get_singleton_tag(self) -> str:
        if not self._view_node:
            return ""
        return self._view_node.GetSingletonTag()

    @classmethod
    def _call_if_value_not_none(cls, setter, value):
        if value is not None:
            setter(value)

    def set_scene(self, scene: vtkMRMLScene) -> None:
        if self._scene == scene:
            return

        self._event_observer.UpdateObserver(self._scene, scene, vtkMRMLScene.EndCloseEvent)
        self._scene = scene
        if self._view_node and self._view_node.GetScene() != scene:
            self._view_node = None

    def reset_camera(self):
        self.first_renderer().ResetCameraScreenSpace()

    def get_view_node_id(self) -> str:
        return self._view_node.GetID() if self._view_node else ""

    def fit_view_to_content(self):
        self.reset_camera()

    def reset_view(self):
        with self.trigger_modified_once():
            self._reset_node_view_properties()
            self.fit_view_to_content()
            self.schedule_render()

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
        self.modified.emit(self)

    @contextmanager
    def trigger_modified_once(self):
        with self.modified.emit_once():
            try:
                yield
            finally:
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
        if not self._view_node:
            return

        if orientation_marker is not None:
            self._view_node.SetOrientationMarkerType(orientation_marker)

        if orientation_marker_size is not None:
            self._view_node.SetOrientationMarkerSize(orientation_marker_size)

    def set_ruler(self, ruler_type: int | None = None, ruler_color: int | None = None):
        """
        Sets the ruler type and color.
        Ruler Enums are defined in the vtkMRMLAbstractViewNode class.
        """
        if not self._view_node:
            return

        if ruler_type is not None:
            self._view_node.SetRulerType(ruler_type)

        if ruler_color is not None:
            self._view_node.SetRulerColor(ruler_color)

    def start_interactor(self) -> None:
        self.interactor().Start()

    @property
    def is_render_blocked(self) -> bool:
        return self._is_render_blocked

    def set_render_blocked(self, is_blocked: bool) -> bool:
        """
        Enable / Disable blocking rendering of the view.
        This method doesn't prevent direct calls to the render_window.Render API.

        :param is_blocked: If True, will prevent all schedule_render calls to render strategy.
            If False, will schedule a new rendering.
        :returns: Previous blocked state
        """
        was_blocked = self._is_render_blocked
        self._is_render_blocked = is_blocked
        if not is_blocked:
            self.schedule_render()
        return was_blocked

    @contextmanager
    def render_blocked(self) -> Generator[None, None, None]:
        """
        Context manager API for blocked rendering in the scope of the call.
        """
        was_blocked = self.set_render_blocked(True)
        yield
        self.set_render_blocked(was_blocked)

    def set_layout_color_from_string(self, color: str):
        self.set_layout_color(self._str_to_color(color))

    def set_layout_color(self, color: list[int]):
        if self._view_node:
            self._view_node.SetLayoutColor(*self._to_float_color(color))

    def set_mapped_in_layout(self, is_mapped_in_layout: bool):
        if self._view_node:
            self._view_node.SetMappedInLayout(is_mapped_in_layout)

    def _on_object_event(self, _obj: vtkObject, _event_id: int, _call_data: Any | None) -> None:
        with self.trigger_modified_once():
            if _obj == self._scene and _event_id == vtkMRMLScene.EndCloseEvent:
                self.reset_view()

    def get_view_node(self) -> vtkMRMLViewNode | None:
        return self._view_node
