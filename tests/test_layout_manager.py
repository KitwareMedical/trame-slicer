from __future__ import annotations

import uuid
from io import BytesIO
from unittest import mock

import pytest
from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch
from playwright.async_api import async_playwright
from slicer import vtkMRMLScene
from trame.app import get_server
from trame.widgets import client, html
from trame_client.ui.core import AbstractLayout
from trame_client.widgets.core import VirtualNode
from trame_vuetify.ui.vuetify3 import VAppLayout

from trame_slicer.core import LayoutManager, SlicerApp, ViewManager
from trame_slicer.rca_view.rca_view_factory import register_rca_factories
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
def a_layout_manager(a_mock_ui, a_mock_view_manager, a_slicer_scene, a_server):
    return LayoutManager(a_slicer_scene, a_mock_view_manager, a_server, virtual_node=a_mock_ui)


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


def test_view_creation_can_be_lazy(a_layout_manager, a_sagittal_layout, a_coronal_layout, a_mock_view_manager):
    a_mock_view_manager.is_view_created.return_value = False
    a_layout_manager.register_layout("id_1", a_sagittal_layout, lazy_initialization=True)
    a_layout_manager.register_layout_dict({"id_2": a_coronal_layout}, lazy_initialization=True)
    a_mock_view_manager.create_view.assert_not_called()


def test_view_creation_is_not_lazy_by_default(
    a_layout_manager, a_sagittal_layout, a_coronal_layout, a_mock_view_manager
):
    a_mock_view_manager.is_view_created.return_value = False
    a_layout_manager.register_layout("id_1", a_sagittal_layout)
    a_layout_manager.register_layout_dict({"id_2": a_coronal_layout})
    assert a_mock_view_manager.create_view.call_count == 2


def test_layout_manager_blocks_views_not_currently_displayed(
    a_slicer_scene, a_view_manager, a_sagittal_layout, a_coronal_layout, a_server
):
    layout_man = LayoutManager(a_slicer_scene, a_view_manager, a_server)
    layout_man.register_layout("id_1", a_sagittal_layout)
    layout_man.register_layout("id_2", a_coronal_layout)

    layout_man.set_layout("id_1")
    assert not a_view_manager.get_view("sagittal_view_tag").is_render_blocked
    assert a_view_manager.get_view("coronal_view_tag").is_render_blocked

    layout_man.set_layout("id_2")
    assert a_view_manager.get_view("sagittal_view_tag").is_render_blocked
    assert not a_view_manager.get_view("coronal_view_tag").is_render_blocked


def server_with_child():
    def _create_app_layout(server, name, color="#000000"):
        app = SlicerApp()
        view = ViewLayoutDefinition(
            "sagittal_view_tag",
            ViewType.SLICE_VIEW,
            ViewProps(orientation="Sagittal", background_color=color),
        )
        layout = Layout(
            LayoutDirection.Vertical,
            [view],
        )

        register_rca_factories(app.view_manager, server)
        layout_manager = LayoutManager(app.scene, app.view_manager, server)

        layout_manager.register_layout("sag_view", layout)
        layout_manager.set_layout("sag_view")

        with AbstractLayout(
            server,
            html.Div(trame_server=server, style="height: 50%;"),
            template_name=name,
        ) as ui:
            layout_manager.initialize_layout_grid(ui)

    server = get_server(f"test_server_{uuid.uuid4()}", client_type="vue3")
    _create_app_layout(
        server,
        "main_app",
    )
    _create_app_layout(server.create_child_server(prefix="child_"), "child_app", "#2B274D")
    with VAppLayout(server):
        client.ServerTemplate(name="main_app")
        client.ServerTemplate(name="child_app")

    return server


def assert_images_differ(img_buffer1: str, img_buffer2: str, threshold: float = 0.1):
    img1 = Image.open(BytesIO(img_buffer1)).convert("RGBA")
    img2 = Image.open(BytesIO(img_buffer2)).convert("RGBA")
    if img1.size != img2.size:
        img2 = img2.resize(img1.size)

    img_diff = Image.new("RGBA", img1.size)
    mismatch = pixelmatch(img1, img2, img_diff, threshold=threshold)
    assert mismatch > threshold


@pytest.mark.asyncio
async def test_layout_manager_is_compatible_with_child_server_pattern():
    parent_server = server_with_child()
    parent_server.start(exec_mode="task", thread=True, open_browser=True)
    assert await parent_server.ready
    assert parent_server.port

    async with async_playwright() as p:
        url = f"http://127.0.0.1:{parent_server.port}/"
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        await page.wait_for_selector("img")
        imgs = page.locator("img")

        count = await imgs.count()
        assert count == 2

        img_buffer1 = await imgs.nth(0).screenshot()
        img_buffer2 = await imgs.nth(1).screenshot()

        assert_images_differ(img_buffer1, img_buffer2)

        await browser.close()
