"""
Minimal trame-slicer example showing how to download data from the server.
Uses a VFileInput for uploading data and the server.protocol.addAttachment to download the data.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from trame.app import TrameApp
from trame_client.widgets.html import Div
from trame_vuetify.ui.vuetify3 import SinglePageLayout
from trame_vuetify.widgets.vuetify3 import VBtn, VFileInput

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories
from trame_slicer.utils import write_client_files_to_dir


class DownloadingTrameSlicerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server)
        self._volume_node = None

        # Slicer application creation
        self._slicer_app = SlicerApp()

        # Remote controlled view factory registration
        register_rca_factories(self._slicer_app.view_manager, self._server)

        # Layout creation and view layout registration
        self._layout_manager = LayoutManager(self._slicer_app.scene, self._slicer_app.view_manager, self._server)

        # Register a layout and set the default view layout
        self._layout_manager.register_layout_dict(LayoutManager.default_grid_configuration())
        self._layout_manager.set_layout("Axial Primary")
        self._build_ui()

    def _build_ui(self):
        with SinglePageLayout(self._server) as self.ui:
            self.ui.root.theme = "dark"

            with self.ui.toolbar:
                self.ui.toolbar.clear()

                with Div(classes="d-flex flex-row align-left mx-4"):
                    VFileInput(
                        change=(
                            f"trigger('{self.server.controller.trigger_name(self._load_files)}', [$event.target.files])"
                        ),
                        prepend_icon="mdi-file-upload",
                        glow=True,
                        multiple=True,
                        hide_input=True,
                        density="compact",
                    )

                    VBtn(
                        icon="mdi-file-download",
                        click=(
                            "utils.download('volume_file.nrrd', trigger('"
                            f"{self.server.controller.trigger_name(self._download_file)}"
                            "'), 'application/octet-stream')"
                        ),
                        variant="plain",
                        hide_details=True,
                        density="compact",
                    )

            with self.ui.content:
                self._layout_manager.initialize_layout_grid(self.ui)

    async def _load_files(self, files: list[dict[str, Any]]) -> None:
        with TemporaryDirectory() as tmp_dir:
            volume_files = sorted(write_client_files_to_dir(files, tmp_dir))
            volume_nodes = self._slicer_app.io_manager.load_volumes(volume_files)
            self._volume_node = volume_nodes[0]
            self._slicer_app.display_manager.show_volume(self._volume_node, do_reset_views=True)

    async def _download_file(self):
        if not self._volume_node:
            return None

        with TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "volume.nrrd"
            self._slicer_app.io_manager.write_volume(self._volume_node, out_path)
            return self._server.protocol.addAttachment(out_path.read_bytes())


if __name__ == "__main__":
    app = DownloadingTrameSlicerApp()
    app.server.start()
