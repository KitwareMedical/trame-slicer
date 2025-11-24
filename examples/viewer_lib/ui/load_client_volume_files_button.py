from dataclasses import dataclass

from trame.widgets import client
from trame_client.widgets.html import Div, Span
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VFileInput, VProgressCircular, VTooltip
from undo_stack import Signal


@dataclass
class LoadClientVolumeFilesButtonState:
    file_loading_busy: bool = False


class LoadClientVolumeFilesButton(Div):
    on_load_client_files = Signal(list[dict])

    def __init__(self):
        super().__init__()
        self._typed_state = TypedState(self.state, LoadClientVolumeFilesButtonState)

        with self:
            client.Style(".v-input__prepend .v-icon { opacity: 1.0; }")  # Overwrite vuetify's opacity
            VFileInput(
                v_bind="props",
                prepend_icon="mdi-folder-open",
                multiple=True,
                hide_input=True,
                change=(
                    f"{self._typed_state.name.file_loading_busy} = true;"
                    "trigger('"
                    f"{self.server.controller.trigger_name(self.on_load_client_files.async_emit)}"
                    "', [$event.target.files]"
                    ")"
                ),
                style="width: 40px; height: 40px; opacity: 1.0;",
                v_if=(f"!{self._typed_state.name.file_loading_busy}",),
            )
            VProgressCircular(v_else=True, indeterminate=True, size=24, style="margin: 8px;")
            with VTooltip(
                activator="parent",
                transition="slide-x-transition",
                location="right",
            ):
                Span("Open files")
