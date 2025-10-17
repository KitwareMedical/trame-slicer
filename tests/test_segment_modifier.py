from __future__ import annotations

import numpy as np
import pytest

from trame_slicer.segmentation import ModificationMode
from trame_slicer.utils import vtk_image_to_np


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


def test_segmentation_modifier(a_segment_modifier, a_segmentation_editor):
    segment_id = a_segmentation_editor.add_empty_segment()
    labelmap = a_segment_modifier.get_segment_labelmap(segment_id, as_numpy_array=True)
    np.testing.assert_array_equal(labelmap.tolist(), [])

    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    modifier[1, 0, 0] = 1

    # Check that writing to the first segment correctly sets its labelmap
    a_segment_modifier.active_segment_id = segment_id
    a_segment_modifier.apply_labelmap(vtk_modifier)
    labelmap = a_segment_modifier.get_segment_labelmap(segment_id, as_numpy_array=True)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[1, 0], [0, 0]]])

    # Check that overwriting at the same location overwrites previous segment
    new_id = a_segmentation_editor.add_empty_segment()
    a_segment_modifier.active_segment_id = new_id
    a_segment_modifier.apply_labelmap(vtk_modifier)
    labelmap = a_segment_modifier.get_segment_labelmap(segment_id, as_numpy_array=True)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[0, 0], [0, 0]]])

    labelmap = a_segment_modifier.get_segment_labelmap(new_id, as_numpy_array=True)
    np.testing.assert_array_equal(labelmap, [[[0, 0], [0, 0]], [[1, 0], [0, 0]]])


@pytest.fixture
def three_arbitrary_segments(a_segment_modifier, a_segmentation_editor):
    s1 = a_segmentation_editor.add_empty_segment()
    s2 = a_segmentation_editor.add_empty_segment()
    s3 = a_segmentation_editor.add_empty_segment()

    # Configure labelmap with arbitrary values
    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    s1_labelmap = [[[1, 0], [0, 0]], [[1, 0], [1, 0]]]
    modifier[:] = s1_labelmap
    a_segment_modifier.active_segment_id = s1
    a_segment_modifier.apply_labelmap(vtk_modifier)

    s2_labelmap = [[[0, 1], [0, 1]], [[0, 0], [0, 0]]]
    modifier[:] = s2_labelmap
    a_segment_modifier.active_segment_id = s2
    a_segment_modifier.apply_labelmap(vtk_modifier)

    s3_labelmap = [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]
    modifier[:] = s3_labelmap
    a_segment_modifier.active_segment_id = s3
    a_segment_modifier.apply_labelmap(vtk_modifier)

    return (s1, s1_labelmap), (s2, s2_labelmap), (s3, s3_labelmap)


def test_segment_modifier_only_erases_active_segment_with_erase_mode(
    a_segment_modifier, a_segmentation_editor, three_arbitrary_segments
):
    (s1, s1_labelmap), (s2, s2_labelmap), (s3, s3_labelmap) = three_arbitrary_segments

    # Erase S3 using modifier for full array
    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)

    a_segment_modifier.active_segment_id = s3
    a_segment_modifier.modification_mode = ModificationMode.Remove
    modifier[:] = 1
    a_segment_modifier.apply_labelmap(vtk_modifier)

    # Assert only the active segment was erased
    np.testing.assert_array_equal(a_segment_modifier.get_segment_labelmap(s1, as_numpy_array=True), s1_labelmap)
    np.testing.assert_array_equal(a_segment_modifier.get_segment_labelmap(s2, as_numpy_array=True), s2_labelmap)
    np.testing.assert_array_equal(
        a_segment_modifier.get_segment_labelmap(s3, as_numpy_array=True), [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]
    )


def test_segment_modifier_erases_all_segments_in_erase_all(
    a_segment_modifier, a_segmentation_editor, three_arbitrary_segments
):
    (s1, s1_labelmap), (s2, s2_labelmap), (s3, s3_labelmap) = three_arbitrary_segments

    # Erase S3 using modifier for full array
    a_segment_modifier.active_segment_id = s3
    a_segment_modifier.modification_mode = ModificationMode.RemoveAll

    vtk_modifier = a_segmentation_editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    modifier[:] = 1
    a_segment_modifier.apply_labelmap(vtk_modifier)

    # Assert all have been removed
    empty = [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]
    np.testing.assert_array_equal(a_segment_modifier.get_segment_labelmap(s1, as_numpy_array=True), empty)
    np.testing.assert_array_equal(a_segment_modifier.get_segment_labelmap(s2, as_numpy_array=True), empty)
    np.testing.assert_array_equal(a_segment_modifier.get_segment_labelmap(s3, as_numpy_array=True), empty)
