import logging
from dataclasses import dataclass, field
from pathlib import Path

from trame.widgets import client
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VFileInput, VProgressCircular, VTooltip
from undo_stack import Signal

from .flex_container import FlexContainer

CHUNK_LOADER_SCRIPT = Path(__file__).with_name("chunk_loader.js")


@dataclass
class LoadVolumeItemsState:
    loading_busy: bool = False
    button_tooltip: bool = False


@dataclass
class LoadVolumeState:
    file_button: LoadVolumeItemsState = field(default_factory=LoadVolumeItemsState)
    dir_button: LoadVolumeItemsState = field(default_factory=LoadVolumeItemsState)


class LoadVolumeUI(FlexContainer):
    on_load_volume = Signal(list[dict])

    def __init__(self, **kwargs):
        kwargs = {"row": True, **kwargs}
        super().__init__(**kwargs)

        typed_state = TypedState(self.state, LoadVolumeState)

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
    on_load_volume = Signal(list[dict])

    def __init__(
        self,
        name: str,
        load_directory: bool,
        icon: str,
        typed_state: TypedState[LoadVolumeItemsState],
        **kwargs,
    ):
        kwargs = {"justify": "center", "row": True, "style": "width: 50px; height: 50px;", **kwargs}
        super().__init__(**kwargs)
        client.register_external_script(
            name="load_files_by_chunks",
            script_file_path=CHUNK_LOADER_SCRIPT,
            function_names=["load_files_by_chunks"],
        )

        self.files = []

        with (
            self,
            client.Handler(
                function="load_files_by_chunks",
                inputs=(f"{{ trigger_name: '{self.server.trigger_name(self.load_chunk)}' }}",),
                completed=(
                    self.on_load_end,
                    "[$event.type, $event.outputs.errorMsg]",
                ),
            ) as client_handler,
        ):
            VTooltip(
                v_model=(typed_state.name.button_tooltip,),
                text=name,
                activator="parent",
                transition="slide-y-transition",
                location="bottom start",
            )
            VFileInput(
                v_if=(f"!{typed_state.name.loading_busy}",),
                change=(
                    f"{typed_state.name.loading_busy} = true;"
                    f"{typed_state.name.button_tooltip} = false;"
                    f"{client_handler.run('$event.target.files')}"
                    ".finally(() => {"
                    f"{typed_state.name.loading_busy} = false;"
                    "});"
                ),
                prepend_icon=icon,
                multiple=not load_directory,
                hide_input=True,
                raw_attrs=["webkitdirectory"] if load_directory else [],
            )
            VProgressCircular(v_else=True, indeterminate=True, size=24)

    async def load_chunk(self, files: list[dict]) -> None:
        if files:
            self.files.extend(files)
        elif self.files:
            # Empty sent files list marks end of upload
            # Emit on_load_volume if any file has been loaded
            await self.on_load_volume.async_emit(self.files)
            self.files = []

    def on_load_end(self, type: str, error_message: str) -> None:
        if type == "success":
            logging.info("Succeeded to load files")
        else:
            logging.error("Failed to load files: %s", error_message)
