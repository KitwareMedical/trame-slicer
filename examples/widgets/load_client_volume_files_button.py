from __future__ import annotations

import asyncio
from tempfile import TemporaryDirectory

from trame_client.widgets.html import Div, Input
from trame_server import Server
from trame_server.utils.asynchronous import create_task
from trame_vuetify.widgets.vuetify3 import VProgressCircular
from vtkmodules.vtkCommonCore import vtkCollection

from trame_slicer.core import SlicerApp
from trame_slicer.utils import write_client_files_to_dir

from .control_button import ControlButton
from .utils import StateId


class LoadClientVolumeFilesButton(Div):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__()
        self._slicer_app = slicer_app
        server.state.setdefault(StateId.file_loading_busy, False)

        with self:
            files_input_ref = "open_files_input"
            Input(
                type="file",
                multiple=True,
                change=(
                    f"{StateId.file_loading_busy} = true;"
                    "trigger('"
                    f"{server.controller.trigger_name(self._create_load_local_files_task)}"
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
                click=lambda: server.js_call(ref=files_input_ref, method="click"),
                v_if=(f"!{StateId.file_loading_busy}",),
            )
            VProgressCircular(v_if=(StateId.file_loading_busy,), indeterminate=True, size=24)

    def _create_load_local_files_task(self, *args, **kwargs):
        self.state[StateId.file_loading_busy] = True
        self.state.flush()

        async def load():
            await asyncio.sleep(1)
            try:
                self._on_load_client_files(*args, **kwargs)
            finally:
                self.state[StateId.file_loading_busy] = False
                self.state.flush()

        create_task(load())

    def _on_load_client_files(self, files: list[dict]) -> None:
        if not files:
            return

        # Remove previous volume nodes
        vol_nodes: vtkCollection = self._slicer_app.scene.GetNodesByClass("vtkMRMLVolumeNode")
        for i_vol in range(vol_nodes.GetNumberOfItems()):
            self._slicer_app.scene.RemoveNode(vol_nodes.GetItemAsObject(i_vol))

        # Load new volumes and display the first one
        with TemporaryDirectory() as tmp_dir:
            volumes = self._slicer_app.io_manager.load_volumes(write_client_files_to_dir(files, tmp_dir))
            if not volumes:
                return

            # Show the largest volume
            def bounds_volume(v):
                b = [0] * 6
                v.GetImageData().GetBounds(b)
                return (b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4])

            volumes = sorted(volumes, key=bounds_volume)
            volume_node = volumes[-1]
            self._slicer_app.display_manager.show_volume(
                volume_node,
                vr_preset=self.state[StateId.vr_preset_value],
                do_reset_views=True,
            )
            self.state[StateId.current_volume_node_id] = volume_node.GetID()
