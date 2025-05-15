from __future__ import annotations

import pytest

from tests.conftest import a_slice_view, a_threed_view
from tests.view_events import ViewEvents
from trame_slicer.segmentation import SegmentationEffectID


def apply_scissors_effect(view):
    view_events = ViewEvents(view)
    center_x, center_y = view_events.view_center()
    view_events.mouse_move_to(center_x, center_y)
    view_events.mouse_press_event()
    view_events.mouse_move_to(0, center_y)
    view_events.mouse_move_to(0, 0)
    view_events.mouse_release_event()


@pytest.mark.parametrize("view", [a_threed_view, a_slice_view])
def test_scissors_effect_can_erase_all_segmentations(
    a_segmentation_editor,
    a_segmentation_model,
    a_volume_node,
    view,
    render_interactive,
    request,
):
    view = request.getfixturevalue(view.__name__)
    a_segmentation_model.SetDisplayVisibility(False)
    segmentation_node = a_segmentation_editor.create_segmentation_node_from_model_node(a_segmentation_model)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)

    labelmap = a_segmentation_editor.get_segment_labelmap(
        a_segmentation_editor.get_segment_ids()[0], as_numpy_array=True
    )

    prev_sum = labelmap.sum()
    a_segmentation_editor.set_active_effect_id(SegmentationEffectID.Scissors)
    apply_scissors_effect(view)

    labelmap = a_segmentation_editor.get_segment_labelmap(
        a_segmentation_editor.get_segment_ids()[0], as_numpy_array=True
    )
    assert labelmap.sum() < prev_sum

    if render_interactive:
        view.interactor().Start()
