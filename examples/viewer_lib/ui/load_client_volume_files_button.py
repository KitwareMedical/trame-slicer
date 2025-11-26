from dataclasses import dataclass

from trame.widgets import client
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VFileInput, VProgressCircular, VTooltip
from undo_stack import Signal

from .utils import FlexContainer


@dataclass
class LoadClientVolumeFilesButtonState:
    file_loading_busy: bool = False


class LoadClientVolumeButtonsDiv(FlexContainer):
    on_load_client_files = Signal(list[dict])
    on_load_client_dir = Signal(list[dict])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self:
            client.Style(".v-input__prepend .v-icon { opacity: 1.0; }")  # Overwrite vuetify's opacity
            self.load_client_volume_files_button = LoadClientVolumeFilesButton(
                name="Open Files", load_directory=False, icon="mdi-file-upload"
            )
            self.load_client_volume_dir_button = LoadClientVolumeFilesButton(
                name="Open Directory", load_directory=True, icon="mdi-folder-upload"
            )

        self.load_client_volume_files_button.on_load_client_items.connect(self.on_load_client_files)
        self.load_client_volume_dir_button.on_load_client_items.connect(self.on_load_client_dir)


class LoadClientVolumeFilesButton(FlexContainer):
    on_load_client_items = Signal(list[dict])

    def __init__(self, name: str, load_directory: bool, icon: str):
        super().__init__(justify="center", row=True, style="width: 35px; height: 35px;")
        self._typed_state = TypedState(self.state, LoadClientVolumeFilesButtonState)

        with self:
            VFileInput(
                v_if=(f"!{self._typed_state.name.file_loading_busy}",),
                change=(
                    f"{self._typed_state.name.file_loading_busy} = true;"
                    "trigger('"
                    f"{self.server.controller.trigger_name(self.on_load_client_items.async_emit)}"
                    "', [$event.target.files]"
                    ")"
                ),
                prepend_icon=icon,
                multiple=not load_directory,
                hide_input=True,
                raw_attrs=["webkitdirectory"] if load_directory else [],
            )
            VProgressCircular(v_else=True, indeterminate=True, size=24)
            VTooltip(
                text=name,
                activator="parent",
                transition="slide-x-transition",
                location="right",
            )
