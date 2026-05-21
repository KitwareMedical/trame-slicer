from dataclasses import dataclass, field

from trame_client.widgets.core import AbstractElement
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    VBtn,
    VCard,
    VCardActions,
    VCardText,
    VCardTitle,
    VColorPicker,
    VDialog,
)
from undo_stack import Signal

from ..text_components import TextField
from .segment_state import SegmentState


@dataclass
class SegmentEditState:
    segment_state: SegmentState = field(default_factory=SegmentState)
    is_color_dialog_visible: bool = False


class SegmentEditUI(AbstractElement):
    color_changed = Signal()
    cancel_clicked = Signal()
    name_changed = Signal()

    def __init__(self, **kwargs):
        super().__init__("segment-edit", **kwargs)
        self._typed_state = TypedState(self.state, SegmentEditState)

        self.name_edit = self._build_name_textfield
        self.color_edit = self._build_color_dialog

    def _build_color_dialog(self, **kwargs):
        with (
            VDialog(v_model=(self._typed_state.name.is_color_dialog_visible,), width="auto", **kwargs),
            VCard() as self.card,
        ):
            VCardTitle("Edit segment", classes="text-center")
            with VCardText():
                VColorPicker(
                    v_model=(self._typed_state.name.segment_state.color,),
                    modes=("['rgb']",),
                )

            with VCardActions(classes="justify-end"):
                VBtn(
                    text="Cancel",
                    prepend_icon="mdi-close",
                    click=self.cancel_clicked,
                )
                VBtn(
                    text="Apply",
                    prepend_icon="mdi-check",
                    click=self.color_changed,
                    variant="tonal",
                )

    def _build_name_textfield(self, **kwargs):
        TextField(
            v_model=(self._typed_state.name.segment_state.name,),
            change=self.name_changed,
            **kwargs,
        )
