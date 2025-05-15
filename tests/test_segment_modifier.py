from __future__ import annotations

import numpy as np
import pytest

from trame_slicer.segmentation import (
    MaskedRegion,
    ModificationMode,
    Segmentation,
    SegmentRegionMask,
    vtk_image_to_np,
)


@pytest.fixture
def a_simple_volume(a_slicer_app, a_data_folder):
    return a_slicer_app.io_manager.load_volumes(a_data_folder.joinpath("simple_volume.nii").as_posix())[-1]


@pytest.fixture
def a_simple_segmentation(a_segmentation_editor, a_simple_volume):
    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_simple_volume)
    return segmentation_node


@pytest.fixture
def a_segment_modifier(a_simple_segmentation, a_segmentation_editor):
    assert a_simple_segmentation
    return a_segmentation_editor.active_segment_modifier


@pytest.fixture
def a_region_mask(a_simple_segmentation, a_volume_node):
    return SegmentRegionMask(Segmentation(a_simple_segmentation, a_volume_node))


def test_segmentation_modifier(a_segment_modifier, a_segmentation_editor):
    segment_id = a_segmentation_editor.add_empty_segment()
    labelmap = a_segment_modifier.get_segment_labelmap(segment_id, as_numpy_array=True)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[0, 0], [0, 0]]])

    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    modifier[1, 0, 0] = 1

    a_segment_modifier.active_segment_id = segment_id
    a_segment_modifier.apply_labelmap(vtk_modifier)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[1, 0], [0, 0]]])

    a_segment_modifier.active_segment_id = a_segmentation_editor.add_empty_segment()
    a_segment_modifier.apply_labelmap(vtk_modifier)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[2, 0], [0, 0]]])


def test_segmentation_modifier_with_mask(a_segment_modifier, a_segmentation_editor):
    a_segment_modifier.mask = np.array([[[True, False], [True, False]], [[True, False], [False, False]]], dtype=np.bool)
    segment_id = a_segmentation_editor.add_empty_segment()
    a_segment_modifier.active_segment_id = segment_id

    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    modifier[1, 0, 0] = 1
    modifier[1, 0, 1] = 1  # out of mask!

    a_segment_modifier.apply_labelmap(vtk_modifier)
    labelmap = a_segment_modifier.get_segment_labelmap(segment_id, as_numpy_array=True)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[1, 0], [0, 0]]])

    a_segment_modifier.active_segment_id = a_segmentation_editor.add_empty_segment()
    a_segment_modifier.apply_labelmap(vtk_modifier)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[2, 0], [0, 0]]])


def test_segment_modifier_only_erases_active_segment_with_erase_mode(a_segment_modifier, a_segmentation_editor):
    s1 = a_segmentation_editor.add_empty_segment()
    a_segmentation_editor.add_empty_segment()
    s3 = a_segmentation_editor.add_empty_segment()

    # Configure labelmap with arbitrary values
    labelmap = a_segment_modifier.get_segment_labelmap(s1, as_numpy_array=True)
    labelmap[:] = [[[1, 2], [3, 2]], [[1, 0], [1, 3]]]

    # Erase S3 using modifier for full array
    a_segment_modifier.active_segment_id = s3
    a_segment_modifier.modification_mode = ModificationMode.Erase

    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    modifier[:] = 1
    a_segment_modifier.apply_labelmap(vtk_modifier)

    # Assert only the active segment was erased
    np.testing.assert_array_equal(labelmap, [[[1, 2], [0, 2]], [[1, 0], [1, 0]]])


def test_segment_modifier_erases_all_segments_in_erase_all(a_segment_modifier, a_segmentation_editor):
    s1 = a_segmentation_editor.add_empty_segment()
    a_segmentation_editor.add_empty_segment()
    s3 = a_segmentation_editor.add_empty_segment()

    # Configure labelmap with arbitrary values
    labelmap = a_segment_modifier.get_segment_labelmap(s1, as_numpy_array=True)
    labelmap[:] = [[[1, 2], [3, 2]], [[1, 0], [1, 3]]]

    # Erase S3 using modifier for full array
    a_segment_modifier.active_segment_id = s3
    a_segment_modifier.modification_mode = ModificationMode.EraseAll

    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    modifier[:] = 1
    a_segment_modifier.apply_labelmap(vtk_modifier)

    # Assert only the active segment was erased
    np.testing.assert_array_equal(labelmap, np.zeros_like(labelmap))


def test_region_mask_with_every_where_returns_array_of_true(a_region_mask, a_segment_modifier, a_segmentation_editor):
    segment_id = a_segmentation_editor.add_empty_segment()
    labelmap = a_segment_modifier.get_segment_labelmap(segment_id, as_numpy_array=True)

    a_region_mask.masked_region = MaskedRegion.EveryWhere
    mask = a_region_mask.get_masked_region(labelmap)
    np.testing.assert_array_equal(mask, [[[1, 1], [1, 1]], [[1, 1], [1, 1]]])


@pytest.fixture
def a_segmentation_with_5_ids(a_segmentation_editor):
    segment_ids = [a_segmentation_editor.add_empty_segment() for _ in range(5)]
    labelmap = a_segmentation_editor.get_segment_labelmap(segment_ids[0], as_numpy_array=True)
    labelmap[:] = [[[0, 1], [2, 3]], [[4, 0], [1, 2]]]
    return segment_ids, labelmap


def test_region_mask_with_selected_segment_ids_returns_only_selected(a_region_mask, a_segmentation_with_5_ids):
    segment_ids, labelmap = a_segmentation_with_5_ids
    a_region_mask.selected_ids = [segment_ids[1], segment_ids[2]]
    a_region_mask.masked_region = MaskedRegion.InsideSelectedSegments
    mask = a_region_mask.get_masked_region(labelmap)
    np.testing.assert_array_equal(mask, [[[0, 0], [1, 1]], [[0, 0], [0, 1]]])


def test_region_outside_selected(a_region_mask, a_segmentation_with_5_ids):
    segment_ids, labelmap = a_segmentation_with_5_ids
    a_region_mask.selected_ids = [segment_ids[1], segment_ids[2]]
    a_region_mask.masked_region = MaskedRegion.OutsideSelectedSegments
    mask = a_region_mask.get_masked_region(labelmap)
    np.testing.assert_array_equal(mask, [[[1, 1], [0, 0]], [[1, 1], [1, 0]]])


def test_region_mask_with_all_segment_returns_not_empty(a_region_mask, a_segmentation_with_5_ids):
    segment_ids, labelmap = a_segmentation_with_5_ids
    a_region_mask.masked_region = MaskedRegion.InsideAllSegments
    mask = a_region_mask.get_masked_region(labelmap)
    np.testing.assert_array_equal(mask, [[[0, 1], [1, 1]], [[1, 0], [1, 1]]])


def test_region_mask_outside_all_segment_returns_empty(a_region_mask, a_segmentation_with_5_ids):
    segment_ids, labelmap = a_segmentation_with_5_ids
    a_region_mask.masked_region = MaskedRegion.OutsideAllSegments
    mask = a_region_mask.get_masked_region(labelmap)
    np.testing.assert_array_equal(mask, [[[1, 0], [0, 0]], [[0, 1], [0, 0]]])


def test_region_mask_can_filter_visible_segments(a_region_mask, a_segmentation_with_5_ids, a_simple_segmentation):
    segment_ids, labelmap = a_segmentation_with_5_ids
    display_node = a_simple_segmentation.GetDisplayNode()
    display_node.SetSegmentVisibility(segment_ids[0], False)
    display_node.SetSegmentVisibility(segment_ids[1], False)

    a_region_mask.masked_region = MaskedRegion.InsideAllVisibleSegments
    mask = a_region_mask.get_masked_region(labelmap)
    np.testing.assert_array_equal(mask, [[[0, 0], [0, 1]], [[1, 0], [0, 0]]])
