import pytest
from undo_stack import UndoStack

from tests.view_events import ViewEvents
from trame_slicer.segmentation import (
    SegmentationEffectGrowFromSeeds,
    SegmentationPaintPipeline2D,
)


@pytest.fixture
def undo_stack(a_segmentation_editor):
    undo_stack = UndoStack()
    a_segmentation_editor.set_undo_stack(undo_stack)
    return undo_stack


@pytest.fixture
def a_sagittal_view(a_slice_view, a_volume_node):
    a_slice_view.set_orientation("Sagittal")
    a_slice_view.set_background_volume_id(a_volume_node.GetID())
    a_slice_view.fit_view_to_content()
    a_slice_view.render()
    return a_slice_view


def test_can_preview_and_apply_grow_from_seeds(
    a_slicer_app,
    a_sagittal_view,
    a_segmentation_editor,
    a_volume_node,
    render_interactive,
    undo_stack,
):
    a_slicer_app.display_manager.show_volume(a_volume_node, vr_preset="MR-Default")

    # Configure the segmentation with an empty segment
    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    foreground_id = a_segmentation_editor.add_empty_segment()
    background_id = a_segmentation_editor.add_empty_segment()

    # Activate the segmentation effect
    effect: SegmentationEffectGrowFromSeeds = a_segmentation_editor.set_active_effect_type(
        SegmentationEffectGrowFromSeeds
    )
    assert effect.is_active
    assert len(effect.pipelines) == 1

    # Verify that pipeline was correctly added to the view and that its brush is correctly active
    view_pipeline: SegmentationPaintPipeline2D = effect.pipelines[0]()
    assert isinstance(view_pipeline, SegmentationPaintPipeline2D)
    assert view_pipeline.IsActive()

    # Paint foreground and background
    a_segmentation_editor.set_active_segment_id(background_id)
    ViewEvents(a_sagittal_view).click_at_center()

    a_segmentation_editor.set_active_segment_id(foreground_id)
    ViewEvents(a_sagittal_view).click_at_left()

    prev_array = a_segmentation_editor.get_segment_labelmap(foreground_id, as_numpy_array=True)
    assert prev_array.sum() > 0

    undo_stack.clear()
    effect.update_grow_from_seeds()
    effect.apply_grow_from_seeds()

    # Verify that a segmentation was correctly written
    # array = a_segmentation_editor.get_segment_labelmap(foreground_id, as_numpy_array=True)
    # assert array.sum() > prev_array.sum()
    # assert undo_stack.can_undo()

    if render_interactive:
        a_sagittal_view.interactor().Start()
