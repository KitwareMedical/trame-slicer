from pathlib import Path

import numpy as np
import pytest
from undo_stack import UndoStack

from trame_slicer.segmentation import SegmentationEffectIslands


@pytest.fixture
def a_segmentation_spheres_file_path(a_data_folder) -> Path:
    return a_data_folder.joinpath("segmentation_spheres.nii.gz")


@pytest.fixture
def effect(a_segmentation_editor):
    effect: SegmentationEffectIslands = a_segmentation_editor.set_active_effect_type(SegmentationEffectIslands)
    return effect


@pytest.fixture
def segment_id(a_segmentation_editor):
    return a_segmentation_editor.get_nth_segment_id(0)


@pytest.fixture(autouse=True)
def set_up(a_slicer_app, a_volume_node, a_segmentation_editor, a_segmentation_spheres_file_path):
    a_slicer_app.display_manager.show_volume(a_volume_node, vr_preset="MR-Default")
    segmentation_node = a_slicer_app.io_manager.load_segmentation(a_segmentation_spheres_file_path)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    undo_stack = UndoStack()
    a_segmentation_editor.set_undo_stack(undo_stack)


def get_segment_array(a_segmentation_editor, segment_id):
    return a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)


def test_keep_biggest_island(a_segmentation_editor, effect, segment_id):
    assert effect.is_active
    source_array = get_segment_array(a_segmentation_editor, segment_id)
    effect.keep_largest_island()
    segment_array = get_segment_array(a_segmentation_editor, segment_id)
    # Assert that application created new zeros
    assert np.count_nonzero(source_array) > np.count_nonzero(segment_array)


def test_split_islands_to_segments(a_segmentation_editor, effect):
    assert effect.is_active
    effect.split_islands_to_segments()
    assert len(a_segmentation_editor.get_segment_ids()) == 3


def test_with_0_min_voxel_size_remove_small_islands_does_nothing(a_segmentation_editor, effect, segment_id):
    assert effect.is_active
    source_array = get_segment_array(a_segmentation_editor, segment_id)
    effect.remove_small_islands(1)
    segment_array = get_segment_array(a_segmentation_editor, segment_id)
    assert np.array_equal(source_array, segment_array)


def test_with_max_min_voxel_size_remove_small_islands_removes_all_islands(a_segmentation_editor, effect, segment_id):
    assert effect.is_active
    effect.remove_small_islands(int(1e15))
    segment_array = get_segment_array(a_segmentation_editor, segment_id)
    assert np.array_equal(segment_array, np.zeros_like(segment_array))
