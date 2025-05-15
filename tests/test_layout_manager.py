from __future__ import annotations

from unittest import mock

import pytest
from slicer import vtkMRMLScene
from trame_client.widgets.core import VirtualNode

from trame_slicer.core import LayoutManager, ViewManager
from trame_slicer.views import (
    Layout,
    LayoutDirection,
    ViewLayoutDefinition,
    ViewProps,
    ViewType,
    pretty_xml,
    vue_layout_to_slicer,
)


@pytest.fixture
def a_sagittal_view():
    return ViewLayoutDefinition(
        "sagittal_view_tag",
        ViewType.SLICE_VIEW,
        ViewProps(orientation="Sagittal"),
    )


@pytest.fixture
def a_coronal_view():
    return ViewLayoutDefinition(
        "coronal_view_tag",
        ViewType.SLICE_VIEW,
        ViewProps(orientation="Coronal"),
    )


@pytest.fixture
def a_mock_view_manager() -> ViewManager:
    return mock.create_autospec(ViewManager)


@pytest.fixture
def a_mock_ui() -> VirtualNode:
    return mock.create_autospec(VirtualNode)


@pytest.fixture
def a_slicer_scene() -> vtkMRMLScene:
    return vtkMRMLScene()


@pytest.fixture
def a_layout_manager(a_mock_ui, a_mock_view_manager, a_slicer_scene):
    return LayoutManager(a_slicer_scene, a_mock_view_manager, a_mock_ui)


@pytest.fixture
def a_sagittal_layout(a_sagittal_view):
    return Layout(
        LayoutDirection.Vertical,
        [a_sagittal_view],
    )


@pytest.fixture
def a_coronal_layout(a_coronal_view):
    return Layout(
        LayoutDirection.Vertical,
        [a_coronal_view],
    )


def test_layouts_can_be_registered_to_layout_manager(
    a_sagittal_view,
    a_layout_manager,
):
    sagittal_layout = Layout(
        LayoutDirection.Horizontal,
        [Layout(LayoutDirection.Vertical, [a_sagittal_view])],
    )

    a_layout_manager.register_layout("Sagittal Only", sagittal_layout)
    assert a_layout_manager.has_layout("Sagittal Only")
    assert a_layout_manager.get_layout("Sagittal Only") == sagittal_layout


def test_changing_layout_triggers_view_creation(
    a_layout_manager,
    a_mock_view_manager,
    a_sagittal_view,
):
    a_mock_view_manager.is_view_created.return_value = False

    sagittal_layout = Layout(
        LayoutDirection.Horizontal,
        [Layout(LayoutDirection.Vertical, [a_sagittal_view])],
    )

    a_layout_manager.register_layout("Sagittal Only", sagittal_layout)
    a_layout_manager.set_layout("Sagittal Only")
    a_mock_view_manager.create_view.assert_called_with(
        a_sagittal_view,
    )


def test_registering_existing_layout_overwrites_older_layout(
    a_layout_manager,
    a_sagittal_layout,
    a_coronal_layout,
):
    a_layout_manager.register_layout("L1", a_sagittal_layout)
    a_layout_manager.register_layout("L1", a_coronal_layout)
    assert a_layout_manager.get_layout("L1") == a_coronal_layout


def test_setting_layout_resets_ui(
    a_layout_manager,
    a_mock_ui,
    a_sagittal_layout,
    a_coronal_layout,
):
    a_layout_manager.register_layout("L1", a_sagittal_layout)
    a_layout_manager.register_layout("L2", a_coronal_layout)
    a_layout_manager.set_layout("L1")
    a_mock_ui.clear.assert_called_once()
    a_layout_manager.set_layout("L2")
    assert a_mock_ui.clear.call_count == 2


def test_changing_layout_to_previous_does_nothing(
    a_layout_manager,
    a_mock_ui,
    a_sagittal_layout,
):
    a_layout_manager.register_layout("L1", a_sagittal_layout)
    for _ in range(4):
        a_layout_manager.set_layout("L1")
    a_mock_ui.clear.assert_called_once()


def test_overwriting_layout_resets_layout_if_is_current(
    a_layout_manager,
    a_mock_ui,
    a_sagittal_layout,
    a_coronal_layout,
):
    a_layout_manager.register_layout("L1", a_sagittal_layout)
    a_layout_manager.set_layout("L1")
    a_layout_manager.register_layout("L1", a_coronal_layout)
    assert a_mock_ui.clear.call_count == 2


def test_current_layout_is_stored_in_scene(
    a_layout_manager,
    a_slicer_scene,
    a_sagittal_layout,
):
    a_layout_manager.register_layout("L1", a_sagittal_layout)
    a_layout_manager.set_layout("L1")
    nodes = a_slicer_scene.GetNodesByClass("vtkMRMLScriptedModuleNode")
    node = nodes.GetItemAsObject(0)
    assert node is not None
    assert node.GetParameter("layout_id") == "L1"
    assert pretty_xml(node.GetParameter("layout_description")) == pretty_xml(vue_layout_to_slicer(a_sagittal_layout))


def test_layout_can_be_restored_from_scene(
    a_layout_manager,
    a_slicer_scene,
    a_mock_ui,
    a_mock_view_manager,
    a_sagittal_layout,
    a_sagittal_view,
):
    node = a_slicer_scene.AddNewNodeByClass("vtkMRMLScriptedModuleNode")
    node.SetParameter("layout_id", "L1")
    node.SetParameter(
        "layout_description",
        pretty_xml(vue_layout_to_slicer(a_sagittal_layout)),
    )
    a_layout_manager.set_layout_from_node(node)

    assert a_layout_manager.has_layout("L1")
    assert a_layout_manager.get_layout("L1") == a_sagittal_layout
    a_mock_ui.clear.assert_called_once()
    a_mock_view_manager.is_view_created.assert_called_once_with(a_sagittal_view.singleton_tag)


def test_sets_current_layout_views_as_active(
    a_layout_manager,
    a_sagittal_layout,
    a_coronal_layout,
    a_sagittal_view,
    a_coronal_view,
    a_mock_view_manager,
):
    a_layout_manager.register_layout("L1", a_sagittal_layout)
    a_layout_manager.register_layout("L2", a_coronal_layout)
    a_layout_manager.set_layout("L1")
    a_mock_view_manager.set_current_view_ids.assert_called_once_with([a_sagittal_view.singleton_tag])
    a_mock_view_manager.set_current_view_ids.reset_mock()

    a_layout_manager.set_layout("L2")
    a_mock_view_manager.set_current_view_ids.assert_called_once_with([a_coronal_view.singleton_tag])
