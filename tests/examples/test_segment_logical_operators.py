import pytest

from examples.viewer_lib.logic import LogicalOperatorsEffectLogic
from examples.viewer_lib.ui import (
    LogicalOperatorsEffectUI,
    LogicalOperatorsSegmentationMode,
    ViewerLayout,
)


@pytest.fixture
def effect_ui(a_server):
    with ViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        return LogicalOperatorsEffectUI()


@pytest.fixture
def effect_logic(a_server, a_slicer_app, effect_ui):
    logic = LogicalOperatorsEffectLogic(a_server, a_slicer_app)
    logic.set_effect_ui(effect_ui)
    return logic


@pytest.mark.parametrize("logical_operator", list(LogicalOperatorsSegmentationMode))
def test_can_apply_island_effect(
    effect_logic,
    effect_ui,
    a_segmentation_nifti_file_path,
    a_segmentation_editor,
    a_slicer_app,
    a_volume_node,
    logical_operator,
):
    segmentation_node = a_slicer_app.io_manager.load_segmentation(a_segmentation_nifti_file_path)
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    effect_logic.set_active()
    effect_ui._typed_state.data.mode = logical_operator
    effect_ui.apply_clicked()
