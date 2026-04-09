from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pytest
from numpy.typing import NDArray

from trame_slicer.segmentation import SegmentationEffectLogicalOperators


@dataclass
class _LogicalEffect:
    effect: SegmentationEffectLogicalOperators
    segment_id1: str
    segment_id2: str
    segment_labelmap1: NDArray
    segment_labelmap2: NDArray


@pytest.fixture
def logical_effect(a_slicer_app, a_segmentation_overlap_file_path, a_volume_node, a_segmentation_editor):
    segmentation_node = a_slicer_app.io_manager.load_segmentation(a_segmentation_overlap_file_path)
    assert segmentation_node is not None

    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    effect = a_segmentation_editor.set_active_effect_type(SegmentationEffectLogicalOperators)

    segment_ids = a_segmentation_editor.get_segment_ids()
    assert len(segment_ids) == 2

    segment_id1 = segment_ids[0]
    segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(segment_id1, as_numpy_array=True)
    segment_id2 = segment_ids[1]
    segment_labelmap2 = a_segmentation_editor.get_segment_labelmap(segment_id2, as_numpy_array=True)

    assert not np.array_equal(segment_labelmap1, segment_labelmap2)
    assert len(np.where(np.logical_and(segment_labelmap1, segment_labelmap2))) > 0  # Intersection

    a_segmentation_editor.set_active_segment_id(segment_id1)

    return _LogicalEffect(
        effect=effect,
        segment_id1=segment_id1,
        segment_id2=segment_id2,
        segment_labelmap1=segment_labelmap1,
        segment_labelmap2=segment_labelmap2,
    )


def test_copy(logical_effect: _LogicalEffect, a_segmentation_editor):
    logical_effect.effect.copy(logical_effect.segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(logical_effect.segment_id1, as_numpy_array=True)
    assert np.array_equal(new_segment_labelmap1, logical_effect.segment_labelmap2)


def test_add(logical_effect: _LogicalEffect, a_segmentation_editor):
    logical_effect.effect.add(logical_effect.segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(logical_effect.segment_id1, as_numpy_array=True)

    assert np.all(new_segment_labelmap1[np.where(logical_effect.segment_labelmap1)])
    assert np.all(new_segment_labelmap1[np.where(logical_effect.segment_labelmap2)])


def test_subtract(logical_effect: _LogicalEffect, a_segmentation_editor):
    logical_effect.effect.subtract(logical_effect.segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(logical_effect.segment_id1, as_numpy_array=True)

    #  No intersection
    assert len(np.where(np.logical_and(new_segment_labelmap1, logical_effect.segment_labelmap2))[0]) == 0
    assert np.sum(new_segment_labelmap1) < np.sum(logical_effect.segment_labelmap1)


def test_intersect(logical_effect: _LogicalEffect, a_segmentation_editor):
    logical_effect.effect.intersect(logical_effect.segment_id2)
    new_segment_labelmap1 = a_segmentation_editor.get_segment_labelmap(logical_effect.segment_id1, as_numpy_array=True)

    #  segment 1 must be contained in segment 2
    assert len(np.where(np.logical_and(new_segment_labelmap1, logical_effect.segment_labelmap2 == 0))[0]) == 0
    assert np.sum(new_segment_labelmap1) < np.sum(logical_effect.segment_labelmap1)


def test_invert(logical_effect: _LogicalEffect, a_segmentation_editor):
    h, w, d = logical_effect.segment_labelmap1.shape
    logical_effect.effect.invert()
    new_segment_labelmap = a_segmentation_editor.get_segment_labelmap(logical_effect.segment_id1, as_numpy_array=True)
    assert np.sum(new_segment_labelmap) == h * w * d - np.sum(logical_effect.segment_labelmap1)


def test_fill(logical_effect: _LogicalEffect, a_segmentation_editor):
    h, w, d = logical_effect.segment_labelmap1.shape
    logical_effect.effect.fill()
    new_segment_labelmap = a_segmentation_editor.get_segment_labelmap(logical_effect.segment_id1, as_numpy_array=True)
    assert np.sum(new_segment_labelmap) == h * w * d


def test_clear(logical_effect: _LogicalEffect, a_segmentation_editor):
    logical_effect.effect.clear()
    new_segment_labelmap = a_segmentation_editor.get_segment_labelmap(logical_effect.segment_id1, as_numpy_array=True)
    assert np.array_equal(new_segment_labelmap, np.zeros_like(new_segment_labelmap))


@pytest.mark.parametrize(
    "operator",
    [
        SegmentationEffectLogicalOperators.add,
        SegmentationEffectLogicalOperators.subtract,
        SegmentationEffectLogicalOperators.copy,
        SegmentationEffectLogicalOperators.intersect,
    ],
)
def test_ref_operators_can_be_called_with_empty_ref_segment(
    logical_effect: _LogicalEffect,
    operator: Callable[[SegmentationEffectLogicalOperators, str | None], None],
):
    ref_segment_id = None
    operator(logical_effect.effect, ref_segment_id)
