import pytest
from undo_stack import UndoStack

from tests.conftest import a_slice_view, a_threed_view
from tests.view_events import MouseButton, ViewEvents
from trame_slicer.segmentation import (
    BrushInteractionMode,
    ScissorsEffectFillMode,
    ScissorsEffectRangeMode,
    SegmentationEffectScissors,
)


@pytest.fixture
def undo_stack(a_segmentation_editor):
    undo_stack = UndoStack()
    a_segmentation_editor.set_undo_stack(undo_stack)
    return undo_stack


def apply_scissors_effect_continuous(view):
    view_events = ViewEvents(view)
    center_x, center_y = view_events.view_center()
    view_events.mouse_move_to(center_x, center_y)
    view_events.mouse_press_event()
    view_events.mouse_move_to(0, center_y)
    view_events.mouse_move_to(0, 0)
    view_events.mouse_release_event()


def apply_scissors_effect_point_by_point(view):
    view_events = ViewEvents(view)
    center_x, center_y = view_events.view_center()
    view_events.click_at_coordinate(center_x, center_y)
    view_events.click_at_coordinate(0, center_y)
    view_events.click_at_coordinate(0, 0)
    view_events.click_at_coordinate(0, 0, mouse_button=MouseButton.Right)


def labelmap_sum_is_inferior(ref, labelmap):
    return labelmap.sum() < ref


def labelmap_sum_is_superior(ref, labelmap):
    return labelmap.sum() > ref


@pytest.mark.parametrize("view", [a_threed_view, a_slice_view])
@pytest.mark.parametrize(
    ("brush_interaction_mode", "apply_function"),
    [
        (BrushInteractionMode.CONTINUOUS, apply_scissors_effect_continuous),
        (BrushInteractionMode.POINT_BY_POINT, apply_scissors_effect_point_by_point),
    ],
)
@pytest.mark.parametrize(
    ("operation", "check"),
    [
        (ScissorsEffectFillMode.ERASE_INSIDE, labelmap_sum_is_inferior),
        (ScissorsEffectFillMode.ERASE_OUTSIDE, labelmap_sum_is_inferior),
        (ScissorsEffectFillMode.FILL_INSIDE, labelmap_sum_is_superior),
        (ScissorsEffectFillMode.FILL_OUTSIDE, labelmap_sum_is_superior),
    ],
)
def test_scissors_effect_can_erase_and_fill(
    a_segmentation_editor,
    a_segmentation_model,
    a_volume_node,
    view,
    brush_interaction_mode,
    apply_function,
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
    effect.set_fill_mode(operation)
    effect.set_brush_interaction_mode(brush_interaction_mode)
    apply_function(view)

    labelmap = a_segmentation_editor.get_segment_labelmap(
        a_segmentation_editor.get_segment_ids()[0], as_numpy_array=True
    )
    assert check(prev_sum, labelmap)

    if render_interactive:
        view.interactor().Start()


@pytest.mark.parametrize(
    ("brush_interaction_mode", "apply_function"),
    [
        (BrushInteractionMode.CONTINUOUS, apply_scissors_effect_continuous),
        (BrushInteractionMode.POINT_BY_POINT, apply_scissors_effect_point_by_point),
    ],
)
def test_scissors_effect_cut_modes(
    a_segmentation_editor,
    a_segmentation_model,
    a_volume_node,
    a_slice_view,
    brush_interaction_mode,
    apply_function,
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
    effect.set_fill_mode(ScissorsEffectFillMode.ERASE_INSIDE)
    effect.set_brush_interaction_mode(brush_interaction_mode)

    parameters = [
        (ScissorsEffectRangeMode.UNLIMITED, None),
        (ScissorsEffectRangeMode.POSITIVE, None),
        (ScissorsEffectRangeMode.NEGATIVE, None),
        (ScissorsEffectRangeMode.SYMMETRIC, 0),
        (ScissorsEffectRangeMode.SYMMETRIC, 9999),
    ]

    sums = []

    for cut_mode, distance in parameters:
        effect.set_range_mode(cut_mode)
        if distance is not None:
            effect.set_symmetric_distance(distance)

        apply_function(a_slice_view)
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


def test_scissors_can_delete_points(
    a_segmentation_editor,
    a_segmentation_model,
    a_volume_node,
    a_slice_view,
    render_interactive,
):
    segmentation_node = a_segmentation_editor.create_segmentation_node_from_model_node(a_segmentation_model)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)

    effect: SegmentationEffectScissors = a_segmentation_editor.set_active_effect_type(SegmentationEffectScissors)
    effect.set_fill_mode(ScissorsEffectFillMode.FILL_INSIDE)
    effect.set_brush_interaction_mode(BrushInteractionMode.POINT_BY_POINT)

    pipeline = effect.pipelines[0]()
    line = pipeline.widget._brush._open_curve
    assert line.n_points == 0

    view_events = ViewEvents(a_slice_view)

    def apply():
        center_x, center_y = view_events.view_center()
        view_events.click_at_coordinate(center_x, center_y)
        view_events.click_at_coordinate(0, center_y)
        view_events.click_at_coordinate(0, 0)

    apply()
    assert line.n_points == 3

    # Assert points are deleted one by one
    # and there are no error when pressing "x" with no points left
    for i in range(4):
        view_events.key_press("x")
        assert line.n_points == max(0, 3 - (i + 1))

    apply()
    view_events.key_press("Escape")
    assert line.n_points == 0

    if render_interactive:
        a_slice_view.interactor().Start()
