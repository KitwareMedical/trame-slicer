import numpy as np
import pytest
from undo_stack import UndoStack

from trame_slicer.segmentation import SegmentationEffectSmoothing
from trame_slicer.utils.vtk_numpy import vtk_image_to_np


@pytest.fixture
def effect(a_segmentation_editor):
    effect: SegmentationEffectSmoothing = a_segmentation_editor.set_active_effect_type(SegmentationEffectSmoothing)
    return effect


@pytest.fixture
def segment_id(a_segmentation_editor):
    return a_segmentation_editor.get_nth_segment_id(0)


@pytest.fixture(autouse=True)
def set_up(a_slicer_app, a_volume_node, a_segmentation_editor, a_segmentation_nifti_file_path):
    a_slicer_app.display_manager.show_volume(a_volume_node, vr_preset="MR-Default")
    segmentation_node = a_slicer_app.io_manager.load_segmentation(a_segmentation_nifti_file_path)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    undo_stack = UndoStack()
    a_segmentation_editor.set_undo_stack(undo_stack)


def get_segment_array(a_segmentation_editor, segment_id):
    return a_segmentation_editor.get_segment_labelmap(segment_id, as_numpy_array=True)


def test_gaussian_smoothing(effect, segment_id):
    labelmap_pre_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    effect.apply_gaussian_smoothing(3.0, segment_id)
    labelmap_post_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    assert np.sum(labelmap_pre_use) != np.sum(labelmap_post_use)


def test_median_smoothing(effect, segment_id):
    labelmap_pre_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    effect.apply_median_smoothing(3.0, segment_id)
    labelmap_post_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    assert np.sum(labelmap_pre_use) != np.sum(labelmap_post_use)


def test_joint_smoothing(effect, segment_id):
    labelmap_pre_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    effect.apply_joint_smoothing(1.0)
    labelmap_post_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    assert np.sum(labelmap_pre_use) != np.sum(labelmap_post_use)


def test_opening(effect, segment_id):
    labelmap_pre_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    effect.apply_opening(3.0, segment_id)
    labelmap_post_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    assert np.sum(labelmap_pre_use) > np.sum(labelmap_post_use)


def test_closing(effect, segment_id):
    labelmap_pre_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    effect.apply_closing(3.0, segment_id)
    labelmap_post_use = vtk_image_to_np(effect.modifier.get_segment_labelmap(segment_id))
    assert np.sum(labelmap_pre_use) < np.sum(labelmap_post_use)
