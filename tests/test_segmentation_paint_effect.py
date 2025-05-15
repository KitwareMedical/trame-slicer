from __future__ import annotations

import pytest

from tests.conftest import a_threed_view
from tests.view_events import ViewEvents
from trame_slicer.segmentation import (
    BrushShape,
    SegmentationEffectID,
    SegmentationPaintEffect,
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

    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    a_segmentation_editor.add_empty_segment()
    segment_id = a_segmentation_editor.add_empty_segment()
    paint_effect: SegmentationPaintEffect = a_segmentation_editor.set_active_effect_id(SegmentationEffectID.Paint)

    assert view in paint_effect._interactors
    paint_effect._brush_model.set_shape(BrushShape.Cylinder)
    a_segmentation_editor.set_active_segment_id(segment_id)

    ViewEvents(view).click_at_center()
    array = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert array.sum() > 0
    assert array.max() == 2

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
    paint_effect: SegmentationPaintEffect = a_segmentation_editor.set_active_effect_id(SegmentationEffectID.Erase)
    a_segmentation_editor.set_surface_representation_enabled(False)

    paint_effect._brush_model.set_shape(BrushShape.Cylinder)

    prev_sum = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True).sum()
    ViewEvents(view).click_at_center()
    array = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert array.sum() < prev_sum

    if render_interactive:
        view.interactor().Start()
