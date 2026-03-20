import numpy as np
import pytest

from trame_slicer.segmentation import SegmentationEffectLogicalOperators


@pytest.fixture
def logical_operatos_effect(a_slicer_app, a_segmentation_overlap_file_path, a_volume_node, a_segmentation_editor):
    segmentation_node = a_slicer_app.io_manager.load_segmentation(a_segmentation_overlap_file_path)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    return a_segmentation_editor.set_active_effect_type(SegmentationEffectLogicalOperators)


def test_copy(
    logical_operatos_effect,
    a_segmentation_editor,
):
    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) == 2

    segment_id1 = segment_ids[0]
    segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)
    segment_id2 = segment_ids[1]
    segment_labelmap2 = a_segmentation_editor.get_segment_labelmap(segment_id2, as_numpy_array=True)

    assert not np.array_equal(segment_labelmap1, segment_labelmap2)

    a_segmentation_editor.set_active_segment_id(segment_id1)

    logical_operatos_effect.copy(segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)

    assert np.array_equal(new_segment_labelmap1, segment_labelmap2)


def test_add(
    logical_operatos_effect,
    a_segmentation_editor,
):
    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) == 2

    segment_id1 = segment_ids[0]
    segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)
    segment_id2 = segment_ids[1]
    segment_labelmap2 = a_segmentation_editor.get_segment_labelmap(segment_id2, as_numpy_array=True)

    assert not np.array_equal(segment_labelmap1, segment_labelmap2)

    a_segmentation_editor.set_active_segment_id(segment_id1)

    logical_operatos_effect.add(segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)

    assert np.all(new_segment_labelmap1[np.where(segment_labelmap1)])
    assert np.all(new_segment_labelmap1[np.where(segment_labelmap2)])


def test_subtract(
    logical_operatos_effect,
    a_segmentation_editor,
):
    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) == 2

    segment_id1 = segment_ids[0]
    segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)
    segment_id2 = segment_ids[1]
    segment_labelmap2 = a_segmentation_editor.get_segment_labelmap(segment_id2, as_numpy_array=True)
    a_segmentation_editor.set_active_segment_id(segment_id1)

    assert not np.array_equal(segment_labelmap1, segment_labelmap2)
    assert len(np.where(np.logical_and(segment_labelmap1, segment_labelmap2))) > 0  # Intersection

    logical_operatos_effect.subtract(segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)
    assert len(np.where(np.logical_and(new_segment_labelmap1, segment_labelmap2))[0]) == 0  #  No intersection
    assert np.sum(new_segment_labelmap1) < np.sum(segment_labelmap1)


def test_intersect(
    logical_operatos_effect,
    a_segmentation_editor,
):
    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) == 2

    segment_id1 = segment_ids[0]
    segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)
    segment_id2 = segment_ids[1]
    segment_labelmap2 = a_segmentation_editor.get_segment_labelmap(segment_id2, as_numpy_array=True)
    a_segmentation_editor.set_active_segment_id(segment_id1)

    assert not np.array_equal(segment_labelmap1, segment_labelmap2)
    assert len(np.where(np.logical_and(segment_labelmap1, segment_labelmap2))) > 0  # Intersection

    logical_operatos_effect.intersect(segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)
    assert (
        len(np.where(np.logical_and(new_segment_labelmap1, segment_labelmap2 == 0))[0]) == 0
    )  #  segment 1 must be contained in segment 2
    assert np.sum(new_segment_labelmap1) < np.sum(segment_labelmap1)


def test_invert(
    logical_operatos_effect,
    a_segmentation_editor,
):
    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) >= 1

    segment_id = segment_ids[0]
    segment_labelmap = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    a_segmentation_editor.set_active_segment_id(segment_id)

    assert np.sum(segment_labelmap) > 0

    h, w, d = segment_labelmap.shape

    logical_operatos_effect.invert()
    new_segment_labelmap = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert np.sum(new_segment_labelmap) == h * w * d - np.sum(segment_labelmap)


def test_fill(
    logical_operatos_effect,
    a_segmentation_editor,
):
    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) >= 1

    segment_id = segment_ids[0]
    a_segmentation_editor.set_active_segment_id(segment_id)

    segment_labelmap = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    h, w, d = segment_labelmap.shape

    logical_operatos_effect.fill()
    new_segment_labelmap = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert np.sum(new_segment_labelmap) == h * w * d


def test_clear(
    logical_operatos_effect,
    a_segmentation_editor,
):
    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) >= 1

    segment_id = segment_ids[0]
    a_segmentation_editor.set_active_segment_id(segment_id)

    logical_operatos_effect.clear()
    new_segment_labelmap = a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)
    assert np.array_equal(new_segment_labelmap, np.zeros_like(new_segment_labelmap))
