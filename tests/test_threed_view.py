from __future__ import annotations

from itertools import product

import pytest
from slicer import vtkMRMLAbstractViewNode


def test_threed_view_can_render_mrml_models(a_threed_view, render_interactive):
    a_threed_view.reset_camera()
    a_threed_view.reset_focal_point()
    a_threed_view.render()

    if render_interactive:
        a_threed_view.start_interactor()


def test_threed_view_can_set_background(a_threed_view, render_interactive):
    a_threed_view.set_background_color([60, 60, 60])
    a_threed_view.set_background_gradient_color([60, 60, 60], [0, 0, 0])
    a_threed_view.set_background_color_from_string("red")
    a_threed_view.set_background_color_from_string(("red", "blue"))

    if render_interactive:
        a_threed_view.start_interactor()


def test_threed_view_can_render_mrml_volumes(
    a_threed_view,
    a_slice_view,
    a_volume_node,
    a_slicer_app,
    render_interactive,
):
    # Use slice view to avoid warnings in test
    a_slice_view.set_background_volume_id(a_volume_node.GetID())
    a_slicer_app.volume_rendering.create_display_node(a_volume_node, "MR-Default")
    a_volume_node.GetDisplayNode().SetVisibility(True)
    a_threed_view.reset_camera()
    a_threed_view.reset_focal_point()
    a_threed_view.render()

    if render_interactive:
        a_threed_view.start_interactor()


def test_threed_view_can_show_orientation_marker(
    a_threed_view,
    render_interactive,
):
    a_threed_view.set_orientation_marker(
        vtkMRMLAbstractViewNode.OrientationMarkerTypeAxes,
        vtkMRMLAbstractViewNode.OrientationMarkerSizeMedium,
    )

    if render_interactive:
        a_threed_view.start_interactor()


def test_three_d_view_can_display_rulers_but_forces_ortho_render_mode(
    a_threed_view,
    render_interactive,
):
    a_threed_view.set_ruler(
        vtkMRMLAbstractViewNode.RulerTypeThick,
        vtkMRMLAbstractViewNode.RulerColorWhite,
    )

    assert not a_threed_view.is_render_mode_perspective()

    if render_interactive:
        a_threed_view.start_interactor()


def test_three_d_view_can_toggle_between_perspective_and_orthographic(
    a_threed_view,
):
    a_threed_view.set_render_mode_to_orthographic()
    assert not a_threed_view.is_render_mode_perspective()
    a_threed_view.set_render_mode_to_perspective()
    assert a_threed_view.is_render_mode_perspective()


@pytest.mark.parametrize(("factor", "is_orthographic"), product([0.9, -3], [True, False]))
def test_three_d_view_can_zoom_by_arbitrary_factor(a_threed_view, render_interactive, factor, is_orthographic):
    if is_orthographic:
        a_threed_view.set_render_mode_to_orthographic()

    def get_zoom():
        camera_node = a_threed_view.get_camera_node()
        return camera_node.GetPosition() if not is_orthographic else camera_node.GetParallelScale()

    prev = get_zoom()
    a_threed_view.zoom(factor)
    assert get_zoom() != prev

    if render_interactive:
        a_threed_view.start_interactor()


@pytest.mark.parametrize("is_orthographic", [True, False])
def test_three_d_view_can_zoom_in(a_threed_view, render_interactive, is_orthographic):
    if is_orthographic:
        a_threed_view.set_render_mode_to_orthographic()

    a_threed_view.zoom_in()

    if render_interactive:
        a_threed_view.start_interactor()


@pytest.mark.parametrize("is_orthographic", [True, False])
def test_three_d_view_can_zoom_out(a_threed_view, render_interactive, is_orthographic):
    if is_orthographic:
        a_threed_view.set_render_mode_to_orthographic()

    a_threed_view.zoom_out()

    if render_interactive:
        a_threed_view.start_interactor()
