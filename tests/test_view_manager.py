from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pytest
from slicer import vtkMRMLApplicationLogic, vtkMRMLScene
from trame.widgets import client
from trame_client.widgets.core import AbstractElement
from trame_client.widgets.html import Div
from trame_vuetify.ui.vuetify3 import SinglePageLayout, VAppLayout
from vtkmodules.vtkCommonCore import vtkCollection

from trame_slicer.core import DisplayManager, LayoutManager, SlicerApp, ViewManager
from trame_slicer.rca_view import RemoteSliceViewFactory, RemoteThreeDViewFactory
from trame_slicer.views import (
    AbstractView,
    AbstractViewChild,
    IViewFactory,
    Layout,
    LayoutDirection,
    SliceView,
    ViewLayout,
    ViewLayoutDefinition,
    ViewProps,
    ViewType,
    create_vertical_slice_view_gutter_ui,
    create_vertical_view_gutter_ui,
)


@pytest.fixture
def a_slicer_app():
    return SlicerApp()


@pytest.fixture
def a_view_manager(a_slicer_app):
    return ViewManager(a_slicer_app.scene, a_slicer_app.app_logic)


@pytest.fixture
def a_2d_view():
    return ViewLayoutDefinition("2d_view", ViewType.SLICE_VIEW, ViewProps())


@pytest.fixture
def a_3d_view():
    return ViewLayoutDefinition("3d_view", ViewType.THREE_D_VIEW, ViewProps())


class FakeFactory(IViewFactory):
    @dataclass
    class View:
        slicer_view: AbstractView = field(default_factory=AbstractView)

    def __init__(self, can_create: bool):
        super().__init__()
        self.can_create = can_create

    def can_create_view(self, _view: ViewLayoutDefinition) -> bool:
        return self.can_create

    def _get_slicer_view(self, view: View) -> AbstractViewChild:
        return view.slicer_view

    def _create_view(
        self,
        _view: ViewLayoutDefinition,
        _scene: vtkMRMLScene,
        _app_logic: vtkMRMLApplicationLogic,
    ) -> View:
        return self.View()


def test_view_manager_uses_first_capable_factory_when_creating_view(
    a_view_manager,
    a_2d_view,
):
    f1 = FakeFactory(can_create=False)
    f2 = FakeFactory(can_create=True)
    f3 = FakeFactory(can_create=True)

    a_view_manager.register_factory(f1)
    a_view_manager.register_factory(f2)
    a_view_manager.register_factory(f3)
    a_view_manager.create_view(a_2d_view)

    assert f2.has_view(a_2d_view.singleton_tag)
    assert not f3.has_view(a_2d_view.singleton_tag)
    assert not f1.has_view(a_2d_view.singleton_tag)


def test_view_manager_returns_existing_view_if_created(a_view_manager, a_2d_view):
    factory = FakeFactory(can_create=True)
    a_view_manager.register_factory(factory)

    v1 = a_view_manager.create_view(a_2d_view)
    v2 = a_view_manager.create_view(a_2d_view)
    assert v1 == v2


def test_view_manager_with_default_factories_created_nodes_are_added_to_slicer_scene(
    a_view_manager,
    a_slicer_app,
    a_2d_view,
    a_3d_view,
    a_server,
):
    a_view_manager.register_factory(RemoteSliceViewFactory(a_server))
    a_view_manager.register_factory(RemoteThreeDViewFactory(a_server))

    slice_view = a_view_manager.create_view(a_2d_view)
    threed_view = a_view_manager.create_view(a_3d_view)

    slice_nodes: vtkCollection = a_slicer_app.scene.GetNodesByClass("vtkMRMLSliceNode")
    assert slice_nodes.GetNumberOfItems() == 1
    assert slice_nodes.GetItemAsObject(0) == slice_view.mrml_view_node

    threed_nodes: vtkCollection = a_slicer_app.scene.GetNodesByClass("vtkMRMLViewNode")
    assert threed_nodes.GetNumberOfItems() == 1
    assert threed_nodes.GetItemAsObject(0) == threed_view.mrml_view_node
    a_server.start()


def test_view_manager_created_views_are_added_to_template(
    a_view_manager,
    a_3d_view,
    a_server,
):
    a_view_manager.register_factory(RemoteThreeDViewFactory(a_server))

    view = a_view_manager.create_view(a_3d_view)
    view.render_window().Render()
    with VAppLayout(a_server):
        client.ServerTemplate(name=a_3d_view.singleton_tag)

    a_server.start()


def test_a_2d_view_factory_creates_views_with_the_right_properties(
    a_view_manager,
    a_server,
):
    a_view_manager.register_factory(RemoteSliceViewFactory(a_server))

    slice_view = ViewLayoutDefinition(
        "view_name",
        ViewType.SLICE_VIEW,
        ViewProps(label="L", orientation="Sagittal", color="#5D8CAE", group=2),
    )
    view = a_view_manager.create_view(slice_view)

    assert view.mrml_view_node.GetOrientation() == "Sagittal"
    assert view.mrml_view_node.GetViewGroup() == 2


def test_2d_factory_views_have_sliders_and_reset_camera_connected_to_slicer(
    a_view_manager,
    a_server,
    a_2d_view,
    a_volume_node,
):
    factory = RemoteSliceViewFactory(a_server, populate_view_ui_f=create_vertical_slice_view_gutter_ui)
    a_view_manager.register_factory(factory)
    view: SliceView = a_view_manager.create_view(a_2d_view)
    view.set_background_volume_id(a_volume_node.GetID())
    vuetify_view = factory.get_factory_view(a_2d_view.singleton_tag).vuetify_view
    vuetify_view_str = str(vuetify_view)
    assert "VSlider" in vuetify_view_str
    assert "VBtn" in vuetify_view_str

    with VAppLayout(a_server):
        client.ServerTemplate(name=a_2d_view.singleton_tag)

    assert "slider_value_2d_view" in vuetify_view_str
    assert "slider_max_2d_view" in vuetify_view_str
    assert "slider_min_2d_view" in vuetify_view_str
    assert "slider_step_2d_view" in vuetify_view_str

    assert a_server.state["slider_value_2d_view"] == view.get_slice_value()

    min_range, max_range = view.get_slice_range()
    assert a_server.state["slider_min_2d_view"] == min_range
    assert a_server.state["slider_max_2d_view"] == max_range
    assert a_server.state["slider_step_2d_view"] == view.get_slice_step()

    view.set_slice_value(42)
    assert a_server.state["slider_value_2d_view"] == 42.0

    a_server.start()


def test_3d_view_factory_has_reset_camera_button(
    a_view_manager,
    a_server,
    a_3d_view,
):
    factory = RemoteThreeDViewFactory(a_server, populate_view_ui_f=create_vertical_view_gutter_ui)
    a_view_manager.register_factory(factory)
    a_view_manager.create_view(a_3d_view)
    view = factory.get_factory_view(a_3d_view.singleton_tag)
    vuetify_view_str = str(view.vuetify_view)
    assert "VBtn" in vuetify_view_str
    a_server.start()


@pytest.mark.parametrize(
    ("view_definition", "scene_id", "name"),
    [
        (ViewLayoutDefinition.axial_view, "vtkMRMLSliceNodeRed", "Red"),
        (ViewLayoutDefinition.coronal_view, "vtkMRMLSliceNodeGreen", "Green"),
        (ViewLayoutDefinition.sagittal_view, "vtkMRMLSliceNodeYellow", "Yellow"),
    ],
)
def test_default_slice_views_names_are_consistent_with_slicer(
    a_view_manager, a_server, view_definition, scene_id, name
):
    a_view_manager.register_factory(RemoteSliceViewFactory(a_server))
    view = a_view_manager.create_view(view_definition())
    assert view
    assert view.mrml_view_node.GetID() == scene_id
    assert view.mrml_view_node.GetName() == name
    assert view.mrml_view_node.GetSingletonTag() == name


@dataclass
class CustomView:
    vuetify_view: AbstractElement


class CustomViews(Enum):
    MY_CUSTOM_VIEW = "CUSTOM"


class CustomViewFactory(IViewFactory):
    def __init__(self, server):
        super().__init__()
        self._server = server

    def _get_slicer_view(self, _view: CustomView) -> AbstractViewChild | None:
        return None

    def can_create_view(self, view: ViewLayoutDefinition) -> bool:
        return view.view_type == CustomViews.MY_CUSTOM_VIEW

    def _create_view(
        self,
        view: ViewLayoutDefinition,
        _scene: vtkMRMLScene,
        _app_logic: vtkMRMLApplicationLogic,
    ) -> CustomView:
        view_id = view.singleton_tag
        with ViewLayout(self._server, template_name=view_id) as vuetify_view:
            Div(classes="fill-width fill-height", style="background-color: blue;")

        return CustomView(vuetify_view)


def custom_view_layout_configuration() -> dict[str, Layout]:
    custom_view = ViewLayoutDefinition("custom_singleton_id", CustomViews.MY_CUSTOM_VIEW, ViewProps())

    return {
        "default": Layout(
            LayoutDirection.Horizontal,
            [
                ViewLayoutDefinition.threed_view(),
                Layout(
                    LayoutDirection.Vertical,
                    [custom_view, (ViewLayoutDefinition.axial_view())],
                ),
            ],
            flex_sizes=["2"],
        )
    }


def test_view_manager_is_compatible_with_non_slicer_views(a_view_manager, a_server, a_slicer_app, a_volume_node):
    # Register view factories
    a_view_manager.register_factory(RemoteSliceViewFactory(a_server))
    a_view_manager.register_factory(RemoteThreeDViewFactory(a_server))
    a_view_manager.register_factory(CustomViewFactory(a_server))

    # Create a layout using the layout manager
    layout_manager = LayoutManager(a_slicer_app.scene, a_view_manager, a_server)

    # Create a display manager
    display_manager = DisplayManager(a_view_manager, a_slicer_app.volume_rendering)

    # Create the layout configuration
    layout_manager.register_layout_dict(custom_view_layout_configuration())

    # Trigger layout change
    layout_manager.set_layout("default")

    with SinglePageLayout(a_server) as ui, ui.content:
        layout_manager.initialize_layout_grid(ui)

    # Show volume
    display_manager.show_volume(a_volume_node)

    # Start server
    a_server.start()


def test_get_view_is_compatible_with_view_node_instance(a_view_manager, a_server, a_2d_view):
    factory = RemoteSliceViewFactory(a_server)
    a_view_manager.register_factory(factory)
    view: SliceView = a_view_manager.create_view(a_2d_view)
    assert a_view_manager.get_view(view.mrml_view_node) == view
