import asyncio
from tempfile import TemporaryDirectory

from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.utils import write_client_files_to_dir

from ..ui import (
    LoadClientVolumeButtonsDiv,
    LoadClientVolumeFilesButtonState,
    StateId,
)
from .base_logic import BaseLogic


class LoadFilesLogic(BaseLogic[LoadClientVolumeFilesButtonState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, LoadClientVolumeFilesButtonState)

    def set_ui(self, ui: LoadClientVolumeButtonsDiv):
        ui.on_load_client_files.connect(self._on_load_client_files)
        ui.on_load_client_dir.connect(self._on_load_client_files)

    async def _on_load_client_files(self, files: list[dict]) -> None:
        self.data.file_loading_busy = True
        await asyncio.sleep(1)

        try:
            self._load_client_files(files)
        finally:
            self._typed_state.data.file_loading_busy = False

    def _load_client_files(self, files: list[dict]) -> None:
        if not files:
            return

        # Remove previous data
        self._slicer_app.scene.Clear()

        # Load new volumes and display the first one
        with TemporaryDirectory() as tmp_dir:
            loaded_files = write_client_files_to_dir(files, tmp_dir)
            if len(loaded_files) == 1 and loaded_files[0].endswith(".mrb"):
                self._on_load_scene(loaded_files[0])
            else:
                self._on_load_volume(loaded_files)

    def _on_load_scene(self, scene_file):
        self._slicer_app.io_manager.load_scene(scene_file)
        self._show_largest_volume(list(self._slicer_app.scene.GetNodesByClass("vtkMRMLVolumeNode")))

    def _on_load_volume(self, loaded_files):
        volumes = self._slicer_app.io_manager.load_volumes(loaded_files)
        if not volumes:
            return
        self._show_largest_volume(volumes)

    def _show_largest_volume(self, volumes):
        if not volumes:
            return

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
        self.state.dirty(StateId.current_volume_node_id)
