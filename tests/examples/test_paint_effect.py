import pytest

from examples.viewer_lib.logic import PaintEffectLogic
from examples.viewer_lib.ui import MedicalViewerLayout, PaintEffectUI
from trame_slicer.segmentation import BrushDiameterMode, SegmentationEffectPaint


@pytest.fixture
def effect_ui(a_server):
    with MedicalViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        return PaintEffectUI()


@pytest.fixture
def effect_logic(a_server, a_slicer_app, a_segmentation_editor, a_volume_node):
    segmentation_node = a_segmentation_editor.create_empty_segmentation_node()
    a_segmentation_editor.set_active_segmentation(segmentation_node, a_volume_node)
    a_segmentation_editor.add_empty_segment()
    return PaintEffectLogic(a_server, a_slicer_app)


def test_can_be_displayed(a_server, a_server_port, effect_ui):
    assert effect_ui
    a_server.start(port=a_server_port)


def test_can_change_brush_size(effect_logic, a_server, a_segmentation_editor):
    a_server.state.ready()

    effect_logic.set_active()
    effect_logic.data.brush_diameter_slider.value = 42
    a_server.state.flush()

    effect = a_segmentation_editor.active_effect
    assert isinstance(effect, SegmentationEffectPaint)

    assert effect.get_brush_diameter() == 42
    assert effect.get_brush_diameter_mode() == BrushDiameterMode.ScreenRelative
