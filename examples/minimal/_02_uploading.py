"""
Minimal trame-slicer example showing how to upload and display a volume.
Uses a VFileInput for uploading data and loading data into the UI.
"""

from tempfile import TemporaryDirectory
from typing import Any

from trame.app import TrameApp
from trame_client.widgets.html import Div
from trame_vuetify.ui.vuetify3 import SinglePageLayout
from trame_vuetify.widgets.vuetify3 import VFileInput

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories
from trame_slicer.utils import write_client_files_to_dir


class UploadingTrameSlicerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server)

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
                        multiple=True,
                        hide_input=True,
                    )

            with self.ui.content:
                self._layout_manager.initialize_layout_grid(self.ui)

    async def _load_files(self, files: list[dict[str, Any]]) -> None:
        with TemporaryDirectory() as tmp_dir:
            volume_files = sorted(write_client_files_to_dir(files, tmp_dir))
            volume_nodes = self._slicer_app.io_manager.load_volumes(volume_files)
            self._slicer_app.display_manager.show_volume(volume_nodes[0], do_reset_views=True)


if __name__ == "__main__":
    app = UploadingTrameSlicerApp()
    app.server.start()
