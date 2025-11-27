import pytest
from trame_vuetify.ui.vuetify3 import SinglePageLayout
from undo_stack import UndoStack

from trame_slicer.core import LayoutManager
from trame_slicer.rca_view import register_rca_factories
from trame_slicer.segmentation import (
    SegmentationEffectThreshold,
    SegmentationThresholdPipeline2D,
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


def test_can_apply_threshold(
    a_sagittal_view,
    a_segmentation_editor,
    a_volume_node,
    render_interactive,
    undo_stack,
):
    # Configure the segmentation with an empty segment
    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    segment_id = a_segmentation_editor.add_empty_segment()

    # Activate the segmentation effect
    effect: SegmentationEffectThreshold = a_segmentation_editor.set_active_effect_type(SegmentationEffectThreshold)
    assert effect.is_active
    assert len(effect.pipelines) == 1

    # Verify that pipeline was correctly added to the view and that its brush is correctly active
    view_pipeline: SegmentationThresholdPipeline2D = effect.pipelines[0]()
    assert isinstance(view_pipeline, SegmentationThresholdPipeline2D)
    assert view_pipeline.IsActive()

    # Activate the segment ID and apply segmentation
    a_segmentation_editor.set_active_segment_id(segment_id)

    undo_stack.clear()
    min_value, max_value = effect.get_threshold_min_max_values()
    effect.auto_threshold()
    assert (min_value, max_value) != effect.get_threshold_min_max_values()
    effect.apply()

    # Verify that a segmentation was correctly written
    array = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert array.sum() > 0
    assert undo_stack.can_undo()

    if render_interactive:
        a_sagittal_view.interactor().Start()


def test_threshold_is_updated_in_async(a_slicer_app, a_segmentation_editor, a_server, a_server_port, a_volume_node):
    a_server.state.ready()

    register_rca_factories(a_slicer_app.view_manager, a_server)

    layout_manager = LayoutManager(a_slicer_app.scene, a_slicer_app.view_manager, a_server)
    layout_manager.register_layout_dict(LayoutManager.default_grid_configuration())
    layout_manager.set_layout("Axial Only")
    a_slicer_app.display_manager.show_volume(a_volume_node)

    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    a_segmentation_editor.add_empty_segment()

    effect: SegmentationEffectThreshold = a_segmentation_editor.set_active_effect_type(SegmentationEffectThreshold)
    effect.auto_threshold()

    with SinglePageLayout(a_server) as ui, ui.content:
        layout_manager.initialize_layout_grid(ui)

    a_server.start(port=a_server_port)
