from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    VBadge,
    VBtn,
    VContainer,
    VLabel,
    VList,
    VListItem,
    VListItemAction,
    VRow,
)
from undo_stack import Signal

from .segment_state import SegmentState


@dataclass
class SegmentListState:
    segments: list[SegmentState] = field(default_factory=list)
    active_segment_id: str = ""


class SegmentList(VContainer):
    """
    List view for the current active segments.
    """

    toggle_segment_visibility_clicked = Signal(str)
    edit_segment_clicked = Signal(str)
    delete_segment_clicked = Signal(str)
    select_segment_clicked = Signal(str)

    def __init__(self, typed_state: TypedState[SegmentListState], **kwargs):
        super().__init__(classes="fill-width pa-0 ma-0", **kwargs)

        with (
            self,
            VList(),
            VListItem(
                classes="pa-0 ma-0",
                v_for=f"(item, i) in {typed_state.name.segments}",
                key="i",
                value="item",
                active=(f"item.segment_id === {typed_state.name.active_segment_id}",),
                click=self._server_trigger(self.select_segment_clicked),
            ),
            VRow(classes="fill-width fill-height pa-0 ma-0"),
        ):
            VBadge(
                classes="mx-2",
                color=("item.color",),
                inline=True,
                bordered=True,
                click=self._server_trigger(self.edit_segment_clicked),
            )

            VLabel("{{ item.name }}", density="compact", style="margin-right: auto; user-select: none; opacity: 1;")

            with VListItemAction():
                VBtn(
                    density="compact",
                    icon=("item.is_visible ? 'mdi-eye-circle-outline' : 'mdi-eye-closed'",),
                    variant="text",
                    click=self._server_trigger(self.toggle_segment_visibility_clicked),
                )
                VBtn(
                    density="compact",
                    icon="mdi-pencil-box-outline",
                    variant="text",
                    click=self._server_trigger(self.edit_segment_clicked),
                )
                VBtn(
                    density="compact",
                    icon="mdi-delete-outline",
                    variant="text",
                    click=self._server_trigger(self.delete_segment_clicked),
                )

    def _server_trigger(self, signal: Signal) -> str:
        return f"trigger('{self.server.trigger_name(signal)}', [item.segment_id]);"
