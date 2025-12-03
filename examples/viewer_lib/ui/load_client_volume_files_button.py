from dataclasses import dataclass

from trame.widgets import client
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VFileInput, VProgressCircular, VTooltip
from undo_stack import Signal

from .utils import FlexContainer


@dataclass
class LoadClientVolumeFilesButtonState:
    loading_busy: bool = False
    button_tooltip: bool = False


class LoadClientVolumeButtonsDiv(FlexContainer):
    on_load_client_files = Signal(list[dict])

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
        self.load_client_volume_dir_button.on_load_client_items.connect(self.on_load_client_files)


class LoadClientVolumeFilesButton(FlexContainer):
    on_load_client_items = Signal(list[dict])

    def __init__(self, name: str, load_directory: bool, icon: str):
        super().__init__(justify="center", row=True, style="width: 35px; height: 35px;")
        self._typed_state = TypedState(
            self.state, LoadClientVolumeFilesButtonState, namespace="folder" if load_directory else "file"
        )

        with self:
            VTooltip(
                v_model=(self._typed_state.name.button_tooltip,),
                text=name,
                activator="parent",
                transition="slide-x-transition",
                location="right",
            )
            VFileInput(
                v_if=(f"!{self._typed_state.name.loading_busy}",),
                change=(
                    f"{self._typed_state.name.loading_busy} = true; {self._typed_state.name.button_tooltip} = false;"
                    "trigger('"
                    f"{self.server.controller.trigger_name(self.on_load_client_items.async_emit)}"
                    f"', [$event.target.files, '{self._typed_state.name.loading_busy}']"
                    ")"
                ),
                prepend_icon=icon,
                multiple=not load_directory,
                hide_input=True,
                raw_attrs=["webkitdirectory"] if load_directory else [],
            )
            VProgressCircular(v_else=True, indeterminate=True, size=24)
