from __future__ import annotations

import pytest

from trame_slicer.core import DisplayManager
from trame_slicer.rca_view.rca_view_factory import register_rca_factories
from trame_slicer.views import (
    SliceView,
    ThreeDView,
    ViewLayoutDefinition,
    ViewProps,
    ViewType,
)


def view_name(group: int, i_view: int, view_type: ViewType):
    return f"{i_view}_{view_type.name}_{group}"


def view_def(group: int, i_view: int, view_type: ViewType):
    return ViewLayoutDefinition(
        view_name(group=group, i_view=i_view, view_type=view_type),
        view_type,
        ViewProps(group=group),
    )


@pytest.fixture
def a_slicer_app_with_two_groups(a_slicer_app, a_server):
    register_rca_factories(a_slicer_app.view_manager, a_server)

    i_view = 0

    for i_group in range(2):
        for _ in range(3):
            assert a_slicer_app.view_manager.create_view(
                view_def(
                    group=i_group,
                    i_view=i_view,
                    view_type=ViewType.SLICE_VIEW,
                )
            )
            i_view += 1

        assert a_slicer_app.view_manager.create_view(
            view_def(
                group=i_group,
                i_view=i_view,
                view_type=ViewType.THREE_D_VIEW,
            )
        )
        i_view += 1

    assert len(a_slicer_app.view_manager.get_slice_views(view_group=0)) == 3
    assert len(a_slicer_app.view_manager.get_threed_views(view_group=0)) == 1
    assert len(a_slicer_app.view_manager.get_slice_views(view_group=1)) == 3
    assert len(a_slicer_app.view_manager.get_threed_views(view_group=1)) == 1

    return a_slicer_app


@pytest.fixture
def slice_view_group_0(a_slicer_app_with_two_groups) -> list[SliceView]:
    return a_slicer_app_with_two_groups.view_manager.get_slice_views(view_group=0)


@pytest.fixture
def slice_view_group_1(a_slicer_app_with_two_groups) -> list[SliceView]:
    return a_slicer_app_with_two_groups.view_manager.get_slice_views(view_group=1)


@pytest.fixture
def threed_view_group_0(a_slicer_app_with_two_groups) -> list[ThreeDView]:
    return a_slicer_app_with_two_groups.view_manager.get_threed_views(view_group=0)


@pytest.fixture
def threed_view_group_1(a_slicer_app_with_two_groups) -> list[ThreeDView]:
    return a_slicer_app_with_two_groups.view_manager.get_threed_views(view_group=1)


def test_a_display_manager_can_show_node_in_given_view_group(
    a_volume_node,
    a_slicer_app_with_two_groups,
    slice_view_group_0,
    slice_view_group_1,
    threed_view_group_0,
    threed_view_group_1,
):
    display_man = DisplayManager(
        a_slicer_app_with_two_groups.view_manager,
        a_slicer_app_with_two_groups.volume_rendering,
    )

    slice_view_group_0[0].set_foreground_volume_id(a_volume_node.GetID())
    display_man.show_volume(a_volume_node, view_group=0)

    assert all(slice_view.get_background_volume_id() == a_volume_node.GetID() for slice_view in slice_view_group_0)

    assert all(slice_view.get_foreground_volume_id() is None for slice_view in slice_view_group_0)

    assert all(slice_view.get_background_volume_id() is None for slice_view in slice_view_group_1)

    display = a_slicer_app_with_two_groups.volume_rendering.get_vr_display_node(a_volume_node)
    assert display
    assert threed_view_group_0[0].get_view_node_id() in display.GetViewNodeIDs()
    assert threed_view_group_1[0].get_view_node_id() not in display.GetViewNodeIDs()


def test_a_display_manager_can_show_node_to_slice_foreground(
    a_volume_node,
    a_slicer_app_with_two_groups,
    slice_view_group_0,
    slice_view_group_1,
):
    display_man = DisplayManager(
        a_slicer_app_with_two_groups.view_manager,
        a_slicer_app_with_two_groups.volume_rendering,
    )
    display_man.show_volume_in_slice_foreground(a_volume_node, view_group=0)

    assert all(slice_view.get_foreground_volume_id() == a_volume_node.GetID() for slice_view in slice_view_group_0)

    assert all(slice_view.get_foreground_volume_id() is None for slice_view in slice_view_group_1)
