import pytest

from examples.viewer_lib.logic import VolumeIntensityRangeMaskEffectLogic
from examples.viewer_lib.ui import ViewerLayout, VolumeIntensityRangeMaskUI


@pytest.fixture
def effect_ui(a_server):
    with ViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        return VolumeIntensityRangeMaskUI()


@pytest.fixture
def effect_logic(a_server, a_slicer_app):
    return VolumeIntensityRangeMaskEffectLogic(a_server, a_slicer_app)


def test_can_be_displayed(a_server, a_server_port, effect_ui):
    assert effect_ui
    a_server.start(port=a_server_port)
