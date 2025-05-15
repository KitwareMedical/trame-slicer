from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest
from slicer import vtkMRMLAbstractViewNode


def test_slice_view_can_display_volume(
    a_slice_view,
    a_volume_node,
    render_interactive,
):
    a_slice_view.set_background_volume_id(a_volume_node.GetID())
    a_slice_view.set_background_color([255, 0, 0])
    a_slice_view.set_orientation("Coronal")
    a_slice_view.fit_view_to_content()

    np.testing.assert_array_almost_equal(a_slice_view.get_slice_range(), [-121.1, 133.9], decimal=1)
    assert a_slice_view.get_slice_step() == 1
    assert a_slice_view.get_slice_value() == pytest.approx(6.9, 0.1)

    a_slice_view.render()
    if render_interactive:
        a_slice_view.start_interactor()


def test_a_slice_view_slice_offset_can_be_set(
    a_slice_view,
    a_volume_node,
):
    a_slice_view.set_background_volume_id(a_volume_node.GetID())
    a_slice_view.set_background_color([255, 0, 0])
    a_slice_view.set_orientation("Coronal")
    a_slice_view.fit_view_to_content()
    a_slice_view.set_slice_value(42)
    assert a_slice_view.get_slice_value() == 42


def test_slice_view_can_display_empty(a_slice_view, render_interactive):
    a_slice_view.set_orientation("Coronal")
    a_slice_view.reset_camera()
    a_slice_view.render()

    if render_interactive:
        a_slice_view.start_interactor()


def test_slice_view_can_register_modified_observers(a_slice_view, a_volume_node):
    mock_obs = MagicMock()
    a_slice_view.add_modified_observer(mock_obs)
    a_slice_view.set_background_volume_id(a_volume_node.GetID())

    a_slice_view.set_orientation("Coronal")

    mock_obs.assert_called_with(a_slice_view)
    mock_obs.reset_mock()

    a_slice_view.remove_modified_observer(mock_obs)

    a_slice_view.set_orientation("Sagittal")
    mock_obs.assert_not_called()


@pytest.mark.xfail(reason="API not available yet")
def test_slice_view_foreground_background_opacity_can_be_set():
    raise NotImplementedError()


def test_slice_view_can_be_set_visible_in_3d(
    a_slice_view,
    a_volume_node,
    render_interactive,
):
    a_slice_view.set_background_volume_id(a_volume_node.GetID())

    assert not a_slice_view.is_visible_in_3d()
    a_slice_view.set_visible_in_3d(True)
    assert a_slice_view.is_visible_in_3d()

    if render_interactive:
        a_slice_view.start_interactor()


def test_slice_view_can_display_orientation_marker(
    a_slice_view,
    render_interactive,
):
    a_slice_view.set_orientation_marker(
        vtkMRMLAbstractViewNode.OrientationMarkerTypeAxes,
        vtkMRMLAbstractViewNode.OrientationMarkerSizeMedium,
    )

    if render_interactive:
        a_slice_view.start_interactor()


def test_slice_view_can_display_rulers(
    a_slice_view,
    render_interactive,
):
    a_slice_view.set_ruler(
        vtkMRMLAbstractViewNode.RulerTypeThick,
        vtkMRMLAbstractViewNode.RulerColorWhite,
    )

    if render_interactive:
        a_slice_view.start_interactor()


@pytest.mark.parametrize("factor", [0.9, -3])
def test_slice_views_can_be_zoomed_in_out_by_arbitrary_factors(
    factor,
    a_slice_view,
    a_volume_node,
    render_interactive,
):
    a_slice_view.set_background_volume_id(a_volume_node.GetID())

    a_slice_view.zoom(factor)

    if render_interactive:
        a_slice_view.start_interactor()


def test_slice_views_can_be_zoomed_in(
    a_slice_view,
    a_volume_node,
    render_interactive,
):
    a_slice_view.set_background_volume_id(a_volume_node.GetID())
    a_slice_view.zoom_in()
    if render_interactive:
        a_slice_view.start_interactor()


def test_slice_views_can_be_zoomed_out(
    a_slice_view,
    a_volume_node,
    render_interactive,
):
    a_slice_view.set_background_volume_id(a_volume_node.GetID())
    a_slice_view.zoom_out()
    if render_interactive:
        a_slice_view.start_interactor()
