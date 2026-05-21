import pytest
from trame_server.utils.typed_state import TypedState

from trame_slicer.app.ui import SegmentEditAreaState, SegmentEditAreaUI, ViewerLayout


@pytest.fixture
def effect_ui(a_server):
    with ViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        return SegmentEditAreaUI(TypedState(a_server.state, SegmentEditAreaState))


def test_can_be_displayed(a_server, a_server_port, effect_ui):
    assert effect_ui
    a_server.start(port=a_server_port)
