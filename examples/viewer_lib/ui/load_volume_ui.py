from dataclasses import dataclass, field

from trame.widgets import client
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VFileInput, VProgressCircular, VTooltip
from undo_stack import Signal

from .flex_container import FlexContainer


@dataclass
class LoadVolumeState:
    loading_busy: bool = False
    button_tooltip: bool = False


@dataclass
class LoadVolumeDivState:
    file_button: LoadVolumeState = field(default_factory=LoadVolumeState)
    dir_button: LoadVolumeState = field(default_factory=LoadVolumeState)


class LoadVolumeDiv(FlexContainer):
    on_load_volume = Signal(list[dict], str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        typed_state = TypedState(self.state, LoadVolumeDivState)

        with self:
            client.Style(".v-input__prepend .v-icon { opacity: 1.0; }")  # Overwrite vuetify's opacity
            self.load_volume_files_button = LoadVolumeButton(
                name="Open Files",
                load_directory=False,
                icon="mdi-file-upload",
                typed_state=typed_state.get_sub_state(typed_state.name.file_button),
            )
            self.load_volume_dir_button = LoadVolumeButton(
                name="Open Directory",
                load_directory=True,
                icon="mdi-folder-upload",
                typed_state=typed_state.get_sub_state(typed_state.name.dir_button),
            )

        self.load_volume_files_button.on_load_volume.connect(self.on_load_volume)
        self.load_volume_dir_button.on_load_volume.connect(self.on_load_volume)


class LoadVolumeButton(FlexContainer):
    on_load_volume = Signal(list[dict], str)

    def __init__(self, name: str, load_directory: bool, icon: str, typed_state: TypedState[LoadVolumeState]):
        super().__init__(justify="center", row=True, style="width: 35px; height: 35px;")

        with self:
            VTooltip(
                v_model=(typed_state.name.button_tooltip,),
                text=name,
                activator="parent",
                transition="slide-x-transition",
                location="right",
            )
            VFileInput(
                v_if=(f"!{typed_state.name.loading_busy}",),
                change=(
                    f"{typed_state.name.loading_busy} = true; {typed_state.name.button_tooltip} = false;"
                    "trigger('"
                    f"{self.server.controller.trigger_name(self.on_load_volume.async_emit)}"
                    f"', [$event.target.files, '{typed_state.name.loading_busy}']"
                    ")"
                ),
                prepend_icon=icon,
                multiple=not load_directory,
                hide_input=True,
                raw_attrs=["webkitdirectory"] if load_directory else [],
            )
            VProgressCircular(v_else=True, indeterminate=True, size=24)
