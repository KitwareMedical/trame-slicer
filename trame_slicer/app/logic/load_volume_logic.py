from tempfile import TemporaryDirectory

from slicer import vtkMRMLVolumeNode
from trame_server import Server
from undo_stack import Signal

from trame_slicer.core import SlicerApp
from trame_slicer.utils import write_client_files_to_dir

from ..ui import (
    LoadVolumeState,
    LoadVolumeUI,
)
from .base_logic import BaseLogic


class LoadVolumeLogic(BaseLogic[LoadVolumeState]):
    volume_loaded = Signal(vtkMRMLVolumeNode)

    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, LoadVolumeState)

    def set_ui(self, ui: LoadVolumeUI):
        ui.on_load_volume.connect(self._on_load_volume)

    def _on_load_volume(self, files: list[dict], is_loading_state_name: str) -> None:
        try:
            self._load_volume_files(files)
        finally:
            self.state[is_loading_state_name] = False

    def _load_volume_files(self, files: list[dict]) -> None:
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
                self._on_load_volume_files(loaded_files)

    def _on_load_scene(self, scene_file):
        self._slicer_app.io_manager.load_scene(scene_file)
        self._show_largest_volume(list(self._slicer_app.scene.GetNodesByClass("vtkMRMLVolumeNode")))

    def _on_load_volume_files(self, loaded_files):
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
            do_reset_views=True,
        )

        self.volume_loaded(volume_node)
