import pytest
from trame_server.utils.typed_state import TypedState

from examples.viewer_lib.logic import SegmentEditDialogLogic
from examples.viewer_lib.ui import (
    MedicalViewerLayout,
    SegmentEditDialog,
    SegmentEditDialogState,
)


@pytest.fixture
def dialog_state(a_server):
    typed_state = TypedState(a_server.state, SegmentEditDialogState)
    typed_state.data.is_visible = True
    typed_state.data.segment_state.name = "Segment Name"
    typed_state.data.segment_state.color = "#FF00FF"
    return typed_state


@pytest.fixture
def dialog(a_server, dialog_state):
    with MedicalViewerLayout(a_server, is_drawer_visible=True):
        return SegmentEditDialog(dialog_state)


@pytest.fixture
def logic(a_server, a_slicer_app, dialog, dialog_state, a_segment_id):
    dialog_state.data.segment_state.segment_id = a_segment_id
    dialog_logic = SegmentEditDialogLogic(a_server, a_slicer_app)
    dialog_logic.set_edit_dialog(dialog)
    return dialog_logic


def test_can_be_displayed(a_server, a_server_port, dialog):
    assert dialog
    a_server.start(port=a_server_port)


def test_on_validate_changes_segment_properties(a_segmentation_editor, dialog, dialog_state, logic):
    assert logic
    dialog.validate_clicked()

    properties = a_segmentation_editor.get_segment_properties(dialog_state.data.segment_state.segment_id)
    assert properties.color_hex.upper() == "#FF00FF"
    assert properties.name == "Segment Name"
    assert not dialog_state.data.is_visible


def test_on_cancel_hides_dialog(a_segmentation_editor, dialog, dialog_state, logic):
    assert logic
    dialog.cancel_clicked()

    properties = a_segmentation_editor.get_segment_properties(dialog_state.data.segment_state.segment_id)
    assert properties.color_hex.upper() != "#FF00FF"
    assert properties.name != "Segment Name"
    assert not dialog_state.data.is_visible
