from dataclasses import dataclass

from trame.widgets.vuetify3 import (
    VBtn,
    VCard,
    VCardActions,
    VCardText,
    VCardTitle,
    VColorPicker,
    VDialog,
)
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal


@dataclass
class ColorDialogState:
    color: str
    is_open: bool = False


class ColorDialog(VDialog):
    apply_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, target_color_state_var: str, mode: str = "rgb", **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, ColorDialogState)
        self.v_model = self._typed_state.name.is_open
        self._target_color_state_var = target_color_state_var
        self._mode = mode

        self._build_ui()

    def _build_ui(self):
        with self, VCard():
            VCardTitle("Edit mask color", classes="text-center")
            with VCardText():
                VColorPicker(
                    v_model=(self._typed_state.name.color,),
                    modes=(f"['{self._mode}']",),
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
                    click=self.apply_clicked,
                    variant="tonal",
                )

    def open(self):
        self._typed_state.data.is_open = True

    def close(self):
        self._typed_state.data.is_open = False

    def get_color(self) -> str:
        return self._typed_state.data.color

    def set_color(self, color: str):
        self._typed_state.data.color = color
