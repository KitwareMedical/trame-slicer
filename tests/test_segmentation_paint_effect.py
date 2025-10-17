from __future__ import annotations

import pytest

from tests.conftest import a_threed_view
from tests.view_events import ViewEvents
from trame_slicer.segmentation import (
    SegmentationEffectErase,
    SegmentationEffectPaint,
)
from trame_slicer.segmentation.segmentation_paint_pipeline import (
    SegmentationPaintPipeline,
)


@pytest.fixture
def a_sagittal_view(a_slice_view, a_volume_node):
    a_slice_view.set_orientation("Sagittal")
    a_slice_view.set_background_volume_id(a_volume_node.GetID())
    a_slice_view.fit_view_to_content()
    a_slice_view.render()
    return a_slice_view


@pytest.mark.parametrize("view", [a_sagittal_view, a_threed_view])
def test_paint_effect_adds_segmentation_to_selected_segment(
    a_slicer_app,
    a_segmentation_editor,
    a_volume_node,
    view,
    request,
    render_interactive,
):
    view = request.getfixturevalue(view.__name__)
    a_slicer_app.display_manager.show_volume(a_volume_node, vr_preset="MR-Default")

    # Configure the segmentation with an empty segment
    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    a_segmentation_editor.add_empty_segment()
    segment_id = a_segmentation_editor.add_empty_segment()

    # Activate the segmentation paint effect
    paint_effect: SegmentationEffectPaint = a_segmentation_editor.set_active_effect_type(SegmentationEffectPaint)

    assert len(paint_effect.pipelines) == 1

    # Verify that pipeline was correctly added to the view and that its brush is correctly active
    view_pipeline: SegmentationPaintPipeline = paint_effect.pipelines[0]()
    assert isinstance(view_pipeline, SegmentationPaintPipeline)
    assert view_pipeline.IsActive()

    # Activate the segment ID and click in the view
    a_segmentation_editor.set_active_segment_id(segment_id)
    ViewEvents(view).click_at_center()

    # Verify that a segmentation was correctly written
    array = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert array.sum() > 0

    if render_interactive:
        a_segmentation_editor.show_3d(True)
        view.interactor().Start()


@pytest.mark.parametrize("view", [a_sagittal_view, a_threed_view])
def test_erase_effect_removes_segmentation_from_selected_segment(
    a_slicer_app,
    a_segmentation_editor,
    a_volume_node,
    a_model_node,
    view,
    request,
    render_interactive,
):
    view = request.getfixturevalue(view.__name__)
    a_slicer_app.display_manager.show_volume(a_volume_node, vr_preset="MR-Default")

    segmentation_node = a_segmentation_editor.create_segmentation_node_from_model_node(model_node=a_model_node)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    segment_id = a_segmentation_editor.get_active_segment_id()
    a_segmentation_editor.set_active_effect_type(SegmentationEffectErase)
    a_segmentation_editor.set_surface_representation_enabled(False)

    prev_sum = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True).sum()
    ViewEvents(view).click_at_center()
    array = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert array.sum() < prev_sum

    if render_interactive:
        view.interactor().Start()
