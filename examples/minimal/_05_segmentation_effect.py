"""
Minimal trame-slicer example showing how to define a new processing segmentation effect.
"""

from tempfile import TemporaryDirectory
from typing import Any

from trame.app import TrameApp
from trame_client.widgets.html import Div
from trame_vuetify.ui.vuetify3 import SinglePageLayout
from trame_vuetify.widgets.vuetify3 import VBtn, VFileInput

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories
from trame_slicer.segmentation import SegmentationEffect, SegmentationEffectPipeline
from trame_slicer.utils import vtk_image_to_np, write_client_files_to_dir


class MyNewEffect(SegmentationEffect):
    def _create_pipeline(
        self,
        _view_node,
        _parameter,
    ) -> SegmentationEffectPipeline | None:
        return None

    def my_apply_method(self):
        # Usually shouldn't mutate the segmentation when not current active
        if not self.is_active:
            return

        # Src VTK image data type
        source_image_data = self.modifier.get_source_image_data()

        # Can be converted to NP (array buffer)
        src_array = vtk_image_to_np(source_image_data)

        # Modifier required for changing the segmentation
        vtk_modifier = self.modifier.create_modifier_labelmap()

        # Can be converted to NP (array buffer)
        modifier = vtk_image_to_np(vtk_modifier)
        modifier[src_array > 42] = 1

        # Apply the label map
        self.modifier.apply_labelmap(vtk_modifier)


class SegmentationEffectTrameSlicerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server)
        self._volume_node = None
        self._segmentation_node = None

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
                        icon="mdi-brush",
                        click=self._on_threshold,
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

    def _on_threshold(self):
        if not self._segmentation_node:
            self._segmentation_node = self._slicer_app.segmentation_editor.create_empty_segmentation_node()

        self._slicer_app.segmentation_editor.set_active_segmentation(self._segmentation_node, self._volume_node)
        self._slicer_app.segmentation_editor.set_surface_representation_enabled(False)

        if not self._slicer_app.segmentation_editor.get_segment_ids():
            self._slicer_app.segmentation_editor.add_empty_segment(segment_name="Segment Name")

        effect: MyNewEffect = self._slicer_app.segmentation_editor.set_active_effect_type(MyNewEffect)
        effect.my_apply_method()


if __name__ == "__main__":
    app = SegmentationEffectTrameSlicerApp()
    app.server.start()
