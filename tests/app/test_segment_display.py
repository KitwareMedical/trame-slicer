from trame_server.utils.typed_state import TypedState

from trame_slicer.app.ui import (
    SegmentDisplayState,
    SegmentDisplayUI,
    ViewerLayout,
)


def test_can_be_displayed(a_server, unused_tcp_port):
    typed_state = TypedState(a_server.state, SegmentDisplayState)

    with ViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        SegmentDisplayUI(typed_state)

    a_server.start(port=unused_tcp_port)
