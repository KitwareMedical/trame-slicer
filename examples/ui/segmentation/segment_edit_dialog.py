from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    VCard,
    VCardActions,
    VCardText,
    VCardTitle,
    VColorPicker,
    VDialog,
    VRow,
    VTextField,
)
from undo_stack import Signal

from ..control_button import ControlButton
from .segment_state import SegmentState


@dataclass
class SegmentEditDialogState:
    segment_state: SegmentState = field(default_factory=SegmentState)
    is_visible: bool = False


class SegmentEditDialog(VDialog):
    validate_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, typed_state: TypedState[SegmentEditDialogState], **kwargs):
        self._typed_state = typed_state
        super().__init__(v_model=(self._typed_state.name.is_visible,), width=300, **kwargs)

        with self, VCard(classes="rounded-xl", style="overflow: hidden;") as self.card:
            VCardTitle("Edit segment", classes="text-center")
            with VCardText():
                with VRow():
                    VTextField(v_model=(self._typed_state.name.segment_state.name,), hide_details="auto")

                with VRow():
                    VColorPicker(
                        v_model=(self._typed_state.name.segment_state.color,),
                        modes=("['rgb']",),
                    )

            with VCardActions(), VRow(style="width: 100%;", align="right"):
                ControlButton(
                    name="Ok",
                    icon="mdi-check",
                    click=self.validate_clicked,
                    size=0,
                    density="comfortable",
                    style="margin-left: auto;",
                )

                ControlButton(
                    name="Cancel",
                    icon="mdi-close",
                    click=self.cancel_clicked,
                    size=0,
                    density="comfortable",
                )
