import pytest

from examples.viewer_lib.logic import IslandsEffectLogic
from examples.viewer_lib.ui import (
    IslandsEffectUI,
    IslandsSegmentationMode,
    MedicalViewerLayout,
)


@pytest.fixture
def effect_ui(a_server):
    with MedicalViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        return IslandsEffectUI()


@pytest.fixture
def effect_logic(a_server, a_slicer_app, effect_ui):
    logic = IslandsEffectLogic(a_server, a_slicer_app)
    logic.set_effect_ui(effect_ui)
    return logic


def test_can_apply_threshold(
    effect_logic, effect_ui, a_segmentation_nifti_file_path, a_segmentation_editor, a_slicer_app, a_volume_node
):
    """Smoke test to ensure all modes are supported"""
    segmentation_node = a_slicer_app.io_manager.load_segmentation(a_segmentation_nifti_file_path)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    effect_logic.set_active()
    for mode in IslandsSegmentationMode:
        effect_ui._typed_state.data.mode = mode.value
        effect_ui.apply_clicked()
        assert True
