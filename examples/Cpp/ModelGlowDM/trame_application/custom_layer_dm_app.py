from tempfile import TemporaryDirectory
from typing import Any

from slicer import vtkMRLMModelGlowLayerDMLogic
from trame.app import TrameApp
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import client
from trame_client.widgets.html import Div
from trame_vuetify.widgets.vuetify3 import VFileInput

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories
from trame_slicer.utils import write_client_files_to_dir


class CustomLayerDMApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")

        self._slicer_app = SlicerApp()
        register_rca_factories(self._slicer_app.view_manager, self._server)

        # Layout creation and view layout registration
        self._layout_manager = LayoutManager(self._slicer_app.scene, self._slicer_app.view_manager, self._server)

        # Register a layout and set the default view layout
        self._layout_manager.register_layout_dict(LayoutManager.default_grid_configuration())
        self._layout_manager.set_layout("3D Only")

        self._build_ui()

        vtkMRLMModelGlowLayerDMLogic.RegisterPipeline(self._slicer_app.scene)

    def _build_ui(self, *_args, **_kwargs):
        with SinglePageLayout(self._server) as self.ui:
            client.Style("html { overflow-y: auto; }")
            self.ui.root.theme = "dark"

            with self.ui.toolbar:
                self.ui.toolbar.clear()

                with Div(classes="d-flex flex-row align-left mx-4"):
                    VFileInput(
                        change=(
                            "trigger('"
                            f"{self.server.controller.trigger_name(self._load_model_files)}"
                            f"', [$event.target.files])"
                        ),
                        prepend_icon="mdi-file-upload",
                        glow=True,
                        multiple=True,
                        hide_input=True,
                        density="compact",
                    )

            with self.ui.content:
                self._layout_manager.initialize_layout_grid(self.ui)

    async def _load_model_files(self, files: list[dict[str, Any]]) -> None:
        with TemporaryDirectory() as tmp_dir:
            model_files = sorted(write_client_files_to_dir(files, tmp_dir))
            for model_file in model_files:
                model_node = self._slicer_app.io_manager.load_model(model_file)
                model_node.CreateDefaultDisplayNodes()
                vtkMRLMModelGlowLayerDMLogic.CreateDisplayNode(model_node, True)


if __name__ == "__main__":
    app = CustomLayerDMApp()
    app.server.start()
