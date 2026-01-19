import pytest
from undo_stack import UndoStack

from tests.conftest import a_slice_view, a_threed_view
from tests.view_events import ViewEvents
from trame_slicer.segmentation import (
    ScissorsSegmentationOperation,
    ScissorsSegmentationSliceCut,
    SegmentationEffectScissors,
)


@pytest.fixture
def undo_stack(a_segmentation_editor):
    undo_stack = UndoStack()
    a_segmentation_editor.set_undo_stack(undo_stack)
    return undo_stack


def apply_scissors_effect(view):
    view_events = ViewEvents(view)
    center_x, center_y = view_events.view_center()
    view_events.mouse_move_to(center_x, center_y)
    view_events.mouse_press_event()
    view_events.mouse_move_to(0, center_y)
    view_events.mouse_move_to(0, 0)
    view_events.mouse_release_event()


def labelmap_sum_is_inferior(ref, labelmap):
    return labelmap.sum() < ref


def labelmap_sum_is_superior(ref, labelmap):
    return labelmap.sum() > ref


@pytest.mark.parametrize("view", [a_threed_view, a_slice_view])
@pytest.mark.parametrize(
    ("operation", "check"),
    [
        (ScissorsSegmentationOperation.ERASE_INSIDE, labelmap_sum_is_inferior),
        (ScissorsSegmentationOperation.ERASE_OUTSIDE, labelmap_sum_is_inferior),
        (ScissorsSegmentationOperation.FILL_INSIDE, labelmap_sum_is_superior),
        (ScissorsSegmentationOperation.FILL_OUTSIDE, labelmap_sum_is_superior),
    ],
)
def test_scissors_effect_can_erase_and_fill(
    a_segmentation_editor,
    a_segmentation_model,
    a_volume_node,
    view,
    operation,
    check,
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
    effect: SegmentationEffectScissors = a_segmentation_editor.set_active_effect_type(SegmentationEffectScissors)
    effect.set_operation(operation)
    apply_scissors_effect(view)

    labelmap = a_segmentation_editor.get_segment_labelmap(
        a_segmentation_editor.get_segment_ids()[0], as_numpy_array=True
    )
    assert check(prev_sum, labelmap)

    if render_interactive:
        view.interactor().Start()


def test_scissors_effect_cut_modes(
    a_segmentation_editor,
    a_segmentation_model,
    a_volume_node,
    a_slice_view,
    undo_stack,
    render_interactive,
):
    a_segmentation_model.SetDisplayVisibility(False)
    segmentation_node = a_segmentation_editor.create_segmentation_node_from_model_node(a_segmentation_model)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)

    labelmap = a_segmentation_editor.get_segment_labelmap(
        a_segmentation_editor.get_segment_ids()[0], as_numpy_array=True
    )

    prev_sum = labelmap.sum()
    effect: SegmentationEffectScissors = a_segmentation_editor.set_active_effect_type(SegmentationEffectScissors)
    effect.set_operation(ScissorsSegmentationOperation.ERASE_INSIDE)

    parameters = [
        (ScissorsSegmentationSliceCut.UNLIMITED, None),
        (ScissorsSegmentationSliceCut.POSITIVE, None),
        (ScissorsSegmentationSliceCut.NEGATIVE, None),
        (ScissorsSegmentationSliceCut.SYMMETRIC, 0),
        (ScissorsSegmentationSliceCut.SYMMETRIC, 9999),
    ]

    sums = []

    for cut_mode, distance in parameters:
        effect.set_cut_mode(cut_mode)
        if distance is not None:
            effect.set_symmetric_distance(distance)

        apply_scissors_effect(a_slice_view)
        labelmap = a_segmentation_editor.get_segment_labelmap(
            a_segmentation_editor.get_segment_ids()[0], as_numpy_array=True
        )
        sums.append(labelmap.sum())

        assert undo_stack.can_undo()
        undo_stack.undo()

    unlimited_sum, positive_sum, negative_sum, zero_distance_symmetric_sum, max_distance_symmetric_sum = sums

    assert unlimited_sum < prev_sum
    assert max_distance_symmetric_sum == unlimited_sum
    assert positive_sum > unlimited_sum
    assert negative_sum > unlimited_sum
    assert zero_distance_symmetric_sum > unlimited_sum

    if render_interactive:
        a_slice_view.interactor().Start()
