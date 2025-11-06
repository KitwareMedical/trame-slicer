from dataclasses import dataclass

from trame_client.widgets.html import Div, Input
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VProgressCircular
from undo_stack import Signal

from .control_button import ControlButton


@dataclass
class LoadClientVolumeFilesButtonState:
    file_loading_busy: bool = False


class LoadClientVolumeFilesButton(Div):
    on_load_client_files = Signal(list[dict])

    def __init__(self):
        super().__init__()
        self._typed_state = TypedState(self.state, LoadClientVolumeFilesButtonState)

        with self:
            files_input_ref = "open_files_input"
            Input(
                type="file",
                multiple=True,
                change=(
                    f"{self._typed_state.name.file_loading_busy} = true;"
                    "trigger('"
                    f"{self.server.controller.trigger_name(self.on_load_client_files.async_emit)}"
                    "', [$event.target.files]"
                    ")"
                ),
                __events=["change"],
                style="display: none;",
                ref=files_input_ref,
            )
            ControlButton(
                name="Open files",
                icon="mdi-folder-open",
                click=lambda: self.server.js_call(ref=files_input_ref, method="click"),
                v_if=(f"!{self._typed_state.name.file_loading_busy}",),
            )
            VProgressCircular(v_if=(self._typed_state.name.file_loading_busy,), indeterminate=True, size=24)
