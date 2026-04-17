from enum import Enum

from trame.widgets import vuetify3 as vuetify
from trame_server.utils.typed_state import TypedState


def enum_to_title(enum: Enum) -> str:
    return enum.name.replace("_", " ").title()


def enum_to_radio_buttons(typed_state: TypedState, enum_type: type[Enum]):
    modes = typed_state.encode(
        [
            {
                "text": enum_to_title(mode),
                "value": mode.value,
            }
            for mode in enum_type
        ]
    )
    vuetify.VRadio(
        v_for=f"mode in {modes}",
        label=("mode.text",),
        value=("mode.value",),
    )
