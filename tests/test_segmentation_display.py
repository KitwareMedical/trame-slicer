from __future__ import annotations

from tests.view_events import ViewEvents
from trame_slicer.segmentation import SegmentationOpacityEnum


def test_segmentation_opacity_can_be_toggled_by_keypress(
    a_slice_view,
    a_segmentation_node,
    render_interactive,
):
    ViewEvents(a_slice_view).key_press("g")
    assert a_segmentation_node.GetDisplayNode().GetOpacity() == 0.0

    ViewEvents(a_slice_view).key_press("g")
    assert a_segmentation_node.GetDisplayNode().GetOpacity() == 1.0

    if render_interactive:
        a_slice_view.interactor().Start()


def test_segmentation_opacity_2d(
    a_slice_view,
    a_segmentation_editor,
    a_segmentation_node,
    render_interactive,
):
    display_node = a_segmentation_node.GetDisplayNode()
    assert display_node is not None

    opacity = 0.5
    a_segmentation_editor.set_2d_opacity(opacity)
    assert display_node.GetOpacity2DFill() == opacity
    assert display_node.GetOpacity2DOutline() == opacity

    if render_interactive:
        a_slice_view.interactor().Start()


def test_segmentation_opacity_3d(
    a_slice_view,
    a_segmentation_editor,
    a_segmentation_node,
    render_interactive,
):
    display_node = a_segmentation_node.GetDisplayNode()
    assert display_node is not None

    opacity = 0.5

    a_segmentation_editor.set_3d_opacity(opacity)
    assert display_node.GetOpacity3D() == opacity

    if render_interactive:
        a_slice_view.interactor().Start()


def test_segmentation_opacity_mode(
    a_slice_view,
    a_segmentation_editor,
    a_segmentation_node,
    render_interactive,
):
    display_node = a_segmentation_node.GetDisplayNode()
    assert display_node is not None

    a_segmentation_editor.set_opacity_mode(SegmentationOpacityEnum.BOTH)
    assert display_node.GetVisibility2DFill()
    assert display_node.GetVisibility2DOutline()

    a_segmentation_editor.set_opacity_mode(SegmentationOpacityEnum.OUTLINE)
    assert not display_node.GetVisibility2DFill()
    assert display_node.GetVisibility2DOutline()

    a_segmentation_editor.set_opacity_mode(SegmentationOpacityEnum.FILL)
    assert display_node.GetVisibility2DFill()
    assert not display_node.GetVisibility2DOutline()

    if render_interactive:
        a_slice_view.interactor().Start()


def test_segment_visibility(
    a_slice_view,
    a_segmentation_editor,
    a_segmentation_node,
    render_interactive,
):
    display_node = a_segmentation_node.GetDisplayNode()
    assert display_node is not None

    a_segmentation_editor.add_empty_segment()
    segment_id = a_segmentation_editor.add_empty_segment()
    assert segment_id != ""

    a_segmentation_editor.set_segment_visibility(segment_id, False)
    assert not display_node.GetSegmentVisibility(segment_id)

    a_segmentation_editor.set_segment_visibility(segment_id, True)
    assert display_node.GetSegmentVisibility(segment_id)

    if render_interactive:
        a_slice_view.interactor().Start()
