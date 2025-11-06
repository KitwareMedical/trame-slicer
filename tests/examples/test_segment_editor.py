import pytest
from trame_server.utils.typed_state import TypedState
from undo_stack import UndoStack

from examples.logic import SegmentEditorLogic
from examples.ui import (
    MedicalViewerLayout,
    SegmentEditorState,
    SegmentEditorUI,
    SegmentState,
)
from trame_slicer.segmentation import (
    SegmentationEffectNoTool,
    SegmentationEffectPaint,
    SegmentationEffectThreshold,
)


@pytest.fixture
def editor_state(a_server):
    return TypedState(a_server.state, SegmentEditorState)


@pytest.fixture
def editor_ui(a_server):
    with MedicalViewerLayout(a_server, is_drawer_visible=True) as ui, ui.drawer:
        editor = SegmentEditorUI()
        editor.effect_button_clicked.connect(lambda *x: print("effect clicked:", *x))
    return editor


@pytest.fixture
def editor_logic(a_server, a_slicer_app, editor_ui, an_active_segmentation, a_segmentation_editor):
    a_segmentation_editor.set_undo_stack(UndoStack(undo_limit=10))
    assert an_active_segmentation
    logic = SegmentEditorLogic(a_server, a_slicer_app)
    logic.set_ui(editor_ui)
    return logic


@pytest.mark.parametrize(
    "active_effect_name",
    [
        SegmentationEffectNoTool.get_effect_name(),
        SegmentationEffectThreshold.get_effect_name(),
        SegmentationEffectPaint.get_effect_name(),
    ],
)
def test_can_be_displayed(a_server, a_server_port, active_effect_name, editor_state, editor_ui):
    assert editor_ui
    editor_state.data.segment_list.segments = [
        SegmentState(is_visible=True, name="heart", color="#FF0000", segment_id="1"),
        SegmentState(is_visible=True, name="lung", color="#00FF00", segment_id="2"),
    ]
    editor_state.data.segment_list.active_segment_id = "2"
    editor_state.data.active_effect_name = active_effect_name
    a_server.start(port=a_server_port)


def test_can_undo_redo(a_segmentation_editor, a_state, editor_logic, editor_state, editor_ui):
    assert editor_logic

    a_state.ready()
    editor_ui.add_segment_clicked()
    a_state.flush()
    assert a_segmentation_editor.get_segment_names()
    assert editor_state.data.can_undo

    editor_ui.undo_clicked()
    a_state.flush()
    assert not editor_state.data.can_undo
    assert editor_state.data.can_redo
    assert not a_segmentation_editor.get_segment_names()

    editor_ui.redo_clicked()
    a_state.flush()
    assert a_segmentation_editor.get_segment_names()
    assert not editor_state.data.can_redo


def test_can_add_remove_segments(a_state, editor_logic, editor_state, editor_ui):
    assert editor_logic

    a_state.ready()
    editor_ui.add_segment_clicked()
    editor_ui.add_segment_clicked()
    a_state.flush()

    assert len(editor_state.data.segment_list.segments) == 2
    editor_ui.delete_segment_clicked(editor_state.data.segment_list.segments[0].segment_id)
    a_state.flush()

    assert len(editor_state.data.segment_list.segments) == 1
