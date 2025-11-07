from trame_server.utils.typed_state import TypedState

from examples.viewer_lib.ui import (
    MedicalViewerLayout,
    SegmentList,
    SegmentListState,
    SegmentState,
)


def test_can_be_displayed(a_server, a_server_port):
    typed_state = TypedState(a_server.state, SegmentListState)
    typed_state.data.segments = [
        SegmentState(is_visible=True, name="heart", color="#FF0000", segment_id="1"),
        SegmentState(is_visible=True, name="lung", color="#00FF00", segment_id="2"),
        SegmentState(is_visible=False, name="brain", color="#0000FF", segment_id="3"),
    ]
    typed_state.data.active_segment_id = "2"

    with MedicalViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        segment_list = SegmentList(typed_state)
        segment_list.edit_segment_clicked.connect(lambda *x: print("edit clicked:", *x))
        segment_list.toggle_segment_visibility_clicked.connect(lambda *x: print("toggle vis clicked:", *x))
        segment_list.delete_segment_clicked.connect(lambda *x: print("delete clicked:", *x))
        segment_list.select_segment_clicked.connect(lambda *x: print("select clicked:", *x))

    a_server.start(port=a_server_port)
