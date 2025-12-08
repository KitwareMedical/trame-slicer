import pytest

from examples.viewer_lib.logic import ThresholdEffectLogic
from examples.viewer_lib.ui import ThresholdEffectUI, ViewerLayout


@pytest.fixture
def effect_ui(a_server):
    with ViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        return ThresholdEffectUI()


@pytest.fixture
def effect_logic(a_server, a_slicer_app, effect_ui):
    logic = ThresholdEffectLogic(a_server, a_slicer_app)
    logic.set_effect_ui(effect_ui)
    return logic


def test_can_be_displayed(a_server, a_server_port, effect_ui):
    assert effect_ui
    a_server.start(port=a_server_port)


def test_can_apply_threshold(effect_logic, effect_ui, a_segmentation_editor, a_segment_id):
    effect_logic.set_active()
    effect_ui.auto_threshold_clicked()
    effect_ui.apply_clicked()

    array = a_segmentation_editor.get_segment_labelmap(a_segment_id, as_numpy_array=True)
    assert array.sum() > 0
