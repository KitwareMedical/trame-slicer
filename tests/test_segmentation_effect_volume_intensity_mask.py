import pytest

from trame_slicer.segmentation import (
    SegmentationEffectNoTool,
    SegmentationEffectThreshold,
    SegmentationEffectVolumeIntensityMask,
    ThresholdParameters,
)
from trame_slicer.utils import create_scripted_module_dataclass_proxy


@pytest.fixture
def editor(a_segmentation_editor):
    return a_segmentation_editor


@pytest.fixture
def active_segmentation_node(editor, a_volume_node):
    segmentation_node = editor.create_empty_segmentation_node()
    editor.set_active_segmentation(segmentation_node, a_volume_node)
    editor.add_empty_segment()
    return segmentation_node


def test_threshold_use_for_volume_intensity_masking(
    editor, a_volume_node, active_segmentation_node, a_slice_view, render_interactive
):
    assert active_segmentation_node
    a_slice_view.set_background_volume_id(a_volume_node.GetID())

    threshold_effect: SegmentationEffectThreshold = editor.set_active_effect_type(SegmentationEffectThreshold)
    mask_effect = editor.get_effect(SegmentationEffectVolumeIntensityMask)

    threshold_effect.set_threshold_min_max_values((0, 100))
    threshold_effect.use_for_volume_intensity_masking()
    editor.set_active_effect_type(SegmentationEffectNoTool)

    assert mask_effect.is_mask_enabled()
    assert mask_effect.is_visible
    assert mask_effect.get_mask_range() == pytest.approx(threshold_effect.get_threshold_min_max_values())

    if render_interactive:
        a_slice_view.start_interactor()


def test_mask_effect_initialization(editor):
    effect = SegmentationEffectVolumeIntensityMask()
    effect.set_editor(editor)
    # Mask is initially disabled, so is_visible should be False
    assert not effect.is_visible


def test_mask_effect_parameters(editor, active_segmentation_node):
    assert active_segmentation_node
    effect = editor.get_effect(SegmentationEffectVolumeIntensityMask)

    # Test mask range
    effect.set_mask_range(10.0, 20.0)
    assert effect.get_mask_range() == (10.0, 20.0)

    # Test mask enabled
    effect.set_mask_enabled(True)
    assert effect.is_mask_enabled() is True

    # Test mask visible
    effect.set_mask_visible(True)
    assert effect.is_visible

    # Verify parameter update (hatch should be True)
    param_node = effect.get_parameter_node()
    proxy = create_scripted_module_dataclass_proxy(ThresholdParameters, param_node, effect._scene)
    assert proxy.hatch is True
    assert proxy.min_value == 10.0
    assert proxy.max_value == 20.0


def test_mask_effect_visibility_toggle(editor, active_segmentation_node):
    assert active_segmentation_node
    effect = editor.get_effect(SegmentationEffectVolumeIntensityMask)

    effect.set_mask_enabled(True)
    effect.set_mask_visible(False)
    assert not effect.is_visible

    effect.set_mask_visible(True)
    assert effect.is_visible
