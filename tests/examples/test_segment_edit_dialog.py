import pytest
from trame_server.utils.typed_state import TypedState

from examples.viewer_lib.logic import SegmentEditLogic
from examples.viewer_lib.ui import (
    SegmentEditState,
    SegmentEditUI,
    ViewerLayout,
)


@pytest.fixture
def segment_edit_state(a_server):
    typed_state = TypedState(a_server.state, SegmentEditState)
    typed_state.data.is_color_dialog_visible = True
    typed_state.data.segment_state.name = "Segment Name"
    typed_state.data.segment_state.color = "#FF00FF"
    return typed_state


@pytest.fixture
def segment_edit(a_server):
    with ViewerLayout(a_server, is_drawer_visible=True):
        return SegmentEditUI()


@pytest.fixture
def logic(a_server, a_slicer_app, segment_edit, segment_edit_state, a_segment_id):
    segment_edit_state.data.segment_state.segment_id = a_segment_id
    segment_edit_logic = SegmentEditLogic(a_server, a_slicer_app)
    segment_edit_logic.set_ui(segment_edit)
    return segment_edit_logic


def test_can_be_displayed(a_server, a_server_port, segment_edit):
    assert segment_edit
    a_server.start(port=a_server_port)


def test_on_validate_color_dialog(a_segmentation_editor, segment_edit, segment_edit_state, logic):
    assert logic
    segment_edit.color_changed()

    properties = a_segmentation_editor.get_segment_properties(segment_edit_state.data.segment_state.segment_id)
    assert properties.color_hex.upper() == "#FF00FF"
    assert not segment_edit_state.data.is_color_dialog_visible


def test_on_cancel_hides_color_dialog(a_segmentation_editor, segment_edit, segment_edit_state, logic):
    assert logic
    segment_edit.cancel_clicked()

    properties = a_segmentation_editor.get_segment_properties(segment_edit_state.data.segment_state.segment_id)
    assert properties.color_hex.upper() != "#FF00FF"
    assert not segment_edit_state.data.is_color_dialog_visible


def test_on_segment_name_edit(a_segmentation_editor, segment_edit, segment_edit_state, logic):
    assert logic
    segment_edit.name_changed()

    properties = a_segmentation_editor.get_segment_properties(segment_edit_state.data.segment_state.segment_id)
    assert properties.name == "Segment Name"
