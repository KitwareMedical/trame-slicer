from pathlib import Path
from tempfile import TemporaryDirectory

from trame_server import Server

from trame_slicer.core import SlicerApp

from ..ui import DownloadSceneButton
from .base_logic import BaseLogic


class DownloadSceneLogic(BaseLogic[None]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, None)

    def set_ui(self, ui: DownloadSceneButton):
        ui.set_download_callback(self._download_scene)

    async def _download_scene(self):
        with TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "scene.mrb"
            self._slicer_app.io_manager.write_scene(out_path)
            return self._server.protocol.addAttachment(out_path.read_bytes())
