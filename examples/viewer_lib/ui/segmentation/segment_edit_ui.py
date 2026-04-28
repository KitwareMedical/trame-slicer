from trame_client.widgets.core import AbstractElement
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from ..color_dialog import ColorDialog
from ..text_components import TextField
from .segment_state import SegmentState


class SegmentEditUI(AbstractElement):
    color_changed = Signal()
    cancel_clicked = Signal()
    name_changed = Signal()

    def __init__(self, **kwargs):
        super().__init__("segment-edit", **kwargs)
        self._typed_state = TypedState(self.state, SegmentState)

    def build_color_dialog(self, **kwargs):
        self.color_dialog = ColorDialog(self._typed_state.name.color, width="auto", **kwargs)
        self.color_dialog.apply_clicked.connect(self.color_changed)
        self.color_dialog.cancel_clicked.connect(self.cancel_clicked)

    def build_name_textfield(self, **kwargs):
        TextField(
            v_model=(self._typed_state.name.name,),
            change=self.name_changed,
            **kwargs,
        )
