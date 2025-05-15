from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from slicer import (
    vtkMRMLModelNode,
    vtkMRMLModelStorageNode,
    vtkMRMLVolumeArchetypeStorageNode,
)
from trame.app import get_server
from trame_client.utils.testing import FixtureHelper
from trame_server.utils.asynchronous import create_task

from tests.direct_view_factory import DirectViewFactory
from trame_slicer.core import SlicerApp
from trame_slicer.views import ViewLayoutDefinition, ViewProps, ViewType


@pytest.fixture
def fixture_helper():
    ROOT_PATH = Path(__file__).parent.parent.absolute()
    return FixtureHelper(ROOT_PATH)


@pytest.fixture
def a_slicer_app():
    return SlicerApp()


@pytest.fixture
def a_segmentation_editor(a_slicer_app):
    return a_slicer_app.segmentation_editor


@pytest.fixture
def a_view_factory():
    return DirectViewFactory()


@pytest.fixture
def a_view_manager(a_slicer_app, a_view_factory):
    a_slicer_app.view_manager.register_factory(a_view_factory)
    return a_slicer_app.view_manager


@pytest.fixture
def a_threed_view(a_view_manager, render_interactive):
    three_d_view = a_view_manager.create_view(
        ViewLayoutDefinition(singleton_tag="ThreeD", type=ViewType.THREE_D_VIEW, properties=ViewProps())
    )
    if render_interactive:
        three_d_view.render_window().ShowWindowOn()
    three_d_view.interactor().UpdateSize(400, 300)
    yield three_d_view
    three_d_view.finalize()


@pytest.fixture
def a_slice_view(a_view_manager, render_interactive):
    view = a_view_manager.create_view(
        ViewLayoutDefinition(
            singleton_tag="Red",
            type=ViewType.SLICE_VIEW,
            properties=ViewProps(orientation="Axial"),
        )
    )
    view.interactor().UpdateSize(400, 300)

    if render_interactive:
        view.render_window().ShowWindowOn()
    return view


@pytest.fixture
def a_data_folder():
    return Path(__file__).parent / "data"


@pytest.fixture
def a_nrrd_volume_file_path(a_data_folder) -> Path:
    return a_data_folder.joinpath("mr_head.nrrd")


@pytest.fixture
def a_nifti_volume_file_path(a_data_folder) -> Path:
    return a_data_folder.joinpath("mr_head.nii.gz")


@pytest.fixture
def ct_chest_dcm_volume_file_paths(a_data_folder) -> list[Path]:
    return list(a_data_folder.joinpath("ct_chest_dcm").glob("*.dcm"))


@pytest.fixture
def mr_head_dcm_volume_file_paths(a_data_folder) -> list[Path]:
    return list(a_data_folder.joinpath("mr_head_dcm").glob("*.dcm"))


@pytest.fixture
def a_model_file_path(a_data_folder) -> Path:
    return a_data_folder.joinpath("model.stl")


@pytest.fixture
def a_segmentation_stl_file_path(a_data_folder) -> Path:
    return a_data_folder.joinpath("segmentation.stl")


@pytest.fixture
def a_segmentation_nifti_file_path(a_data_folder) -> Path:
    return a_data_folder.joinpath("segmentation.nii.gz")


@pytest.fixture
def a_model_node(a_slicer_app, a_model_file_path):
    return load_model_node(
        a_model_file_path.as_posix(),
        a_slicer_app,
    )


def load_model_node(file_path, a_slicer_app):
    storage_node = vtkMRMLModelStorageNode()
    storage_node.SetFileName(file_path)
    model_node: vtkMRMLModelNode = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode")
    storage_node.ReadData(model_node)
    model_node.CreateDefaultDisplayNodes()
    return model_node


@pytest.fixture
def a_segmentation_model(a_slicer_app, a_data_folder):
    return load_model_node(
        a_data_folder.joinpath("segmentation.stl").as_posix(),
        a_slicer_app,
    )


@pytest.fixture
def a_volume_node(a_slicer_app, a_nrrd_volume_file_path):
    storage_node = vtkMRMLVolumeArchetypeStorageNode()
    node = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    storage_node.SetFileName(
        a_nrrd_volume_file_path.as_posix(),
    )
    storage_node.ReadData(node)
    node.SetAndObserveStorageNodeID(storage_node.GetID())

    return node


@pytest.fixture
def a_segmentation_node(a_segmentation_editor, a_volume_node):
    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    return segmentation_node


def pytest_addoption(parser):
    parser.addoption("--render_interactive", action="store", default=0)


@pytest.fixture(scope="session")
def render_interactive(pytestconfig):
    return float(pytestconfig.getoption("render_interactive"))


@pytest.fixture
def a_server(render_interactive):
    server = get_server(None, client_type="vue3")

    async def stop_server(stop_time_s):
        await server.ready
        await asyncio.sleep(stop_time_s)
        await server.stop()

    _server_start = server.start

    def limited_time_start(*args, **kwargs):
        interactive_time_s = max(0.1, render_interactive)
        create_task(stop_server(stop_time_s=interactive_time_s))

        # If render interactive time is very small, opening browser may make the tests hang.
        # For rendering time less than 1 second, disable browser opening.
        open_browser = bool(render_interactive > 1)
        _server_start(*args, open_browser=open_browser, **kwargs)

    server.start = limited_time_start

    try:
        yield server
    finally:
        server.start = _server_start


@pytest.fixture
def a_subprocess_server(xprocess, server_path, fixture_helper):
    name, Starter, Monitor = fixture_helper.get_xprocess_args(server_path)

    # ensure process is running and return its logfile
    logfile = xprocess.ensure(name, Starter)
    try:
        yield Monitor(logfile[1])
    finally:
        # clean up whole process tree afterwards
        xprocess.getinfo(name).terminate()
