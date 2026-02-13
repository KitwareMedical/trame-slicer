import pytest

from tests.conftest import a_slice_view, a_threed_view
from tests.view_events import MouseButton, ViewEvents
from trame_slicer.segmentation import SegmentationEffectDraw


def apply_draw_effect(view):
    view_events = ViewEvents(view)
    center_x, center_y = view_events.view_center()
    view_events.mouse_move_to(center_x, center_y)
    view_events.mouse_press_event()
    view_events.mouse_release_event()
    view_events.mouse_move_to(0, center_y)
    view_events.mouse_press_event()
    view_events.mouse_release_event()
    view_events.mouse_move_to(0, 0)
    view_events.mouse_press_event()
    view_events.mouse_release_event()
    view_events.mouse_press_event(MouseButton.Right)


@pytest.mark.parametrize("view", [a_slice_view, a_threed_view])
def test_draw_effect_adds_segmentation_to_selected_segment(
    a_slicer_app,
    a_segmentation_editor,
    a_volume_node,
    view,
    request,
    render_interactive,
):
    view = request.getfixturevalue(view.__name__)
    a_slicer_app.display_manager.show_volume(a_volume_node, vr_preset="MR-Default")

    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    segment_id = a_segmentation_editor.add_empty_segment()
    a_segmentation_editor.set_active_segment_id(segment_id)
    a_segmentation_editor.set_active_effect_type(SegmentationEffectDraw)
    apply_draw_effect(view)
    array = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert array.sum() > 0

    if render_interactive:
        a_segmentation_editor.show_3d(True)
        view.interactor().Start()
