from dataclasses import dataclass, field

from trame.widgets import client
from trame.widgets.vuetify3 import (
    Template,
    VIcon,
    VList,
    VListItem,
)
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from ..utils import TextField
from .segment_edit_ui import SegmentEditUI
from .segment_state import SegmentState


@dataclass
class SegmentListState:
    segments: list[SegmentState] = field(default_factory=list)
    active_segment_id: str = ""


class SegmentList(VList):
    """
    List view for the current active segments.
    """

    toggle_segment_visibility_clicked = Signal(str)
    edit_segment_color_clicked = Signal(str)
    delete_segment_clicked = Signal(str)
    select_segment_clicked = Signal(str)

    def __init__(self, typed_state: TypedState[SegmentListState], **kwargs):
        super().__init__(**kwargs)
        self.edit_ui = SegmentEditUI()

        with self:
            client.Style(".v-list-item__prepend { display: grid }")
            with VListItem(
                v_for=f"(item, i) in {typed_state.name.segments}",
                key="i",
                value="item",
                active=(f"item.segment_id === {typed_state.name.active_segment_id}",),
                click=self._server_trigger(self.select_segment_clicked),
            ):
                with Template(v_slot_prepend=True):
                    VIcon(
                        icon="mdi-circle",
                        color=("item.color",),
                        click=self._server_trigger(self.edit_segment_color_clicked),
                    )

                with Template(v_slot_default=True):
                    TextField(
                        v_if=(f"item.segment_id !== {typed_state.name.active_segment_id}",),
                        disabled=True,
                        v_model=("item.name",),
                    )
                    self.edit_ui._build_name_textfield(
                        v_else=True,
                    )

                with Template(v_slot_append=True):
                    VIcon(
                        classes="mr-2",
                        icon=("item.is_visible ? 'mdi-eye-outline' : 'mdi-eye-off-outline'",),
                        click=self._server_trigger(self.toggle_segment_visibility_clicked),
                    )
                    VIcon(
                        icon="mdi-delete-outline",
                        click=self._server_trigger(self.delete_segment_clicked),
                    )

    def _server_trigger(self, signal: Signal) -> str:
        return f"trigger('{self.server.trigger_name(signal)}', [item.segment_id]);"
