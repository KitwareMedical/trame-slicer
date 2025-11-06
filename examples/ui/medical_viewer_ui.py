from typing import Any

from trame_client.widgets.html import Div
from trame_server import Server

from trame_slicer.core import LayoutManager, SlicerApp

from .control_button import ControlButton
from .layout_button import LayoutButton
from .load_client_volume_files_button import LoadClientVolumeFilesButton
from .markups_button import MarkupsButton
from .medical_viewer_layout import MedicalViewerLayout
from .mpr_interaction_button import MprInteractionButton
from .segmentation import SegmentEditorUI
from .slab_button import SlabButton
from .volume_property_button import VolumePropertyButton


class MedicalViewerUI:
    def __init__(self, server: Server, slicer_app: SlicerApp, layout_manager: LayoutManager):
        with MedicalViewerLayout(server) as self.layout:
            with self.layout.toolbar:
                self.load_client_volume_files_button = LoadClientVolumeFilesButton()
                self.volume_property_button = VolumePropertyButton(server=server, slicer_app=slicer_app)
                self.layout_button = LayoutButton()
                self.markups_button = MarkupsButton()
                self._create_drawer_ui_button(icon="mdi-brush", name="Segmentation", ui_type=SegmentEditorUI)
                self.slab_button = SlabButton()
                self.mpr_interaction_button = MprInteractionButton()

            with self.layout.drawer:
                self.segment_editor_ui = self._register_drawer_ui(SegmentEditorUI)

            with self.layout.content, Div(classes="fill-height d-flex flex-row flex-grow-1"):
                layout_manager.initialize_layout_grid(self.layout)

    def _register_drawer_ui(self, ui_type: type) -> Any:
        return ui_type(v_if=(f"{self.layout.typed_state.name.active_drawer_ui} === '{ui_type.__name__}'",))

    def _create_drawer_ui_button(self, *, name: str, icon: str | tuple, ui_type: type):
        async def change_drawer_ui():
            self.layout.typed_state.data.active_drawer_ui = ui_type.__name__
            self.layout.typed_state.data.is_drawer_visible = True

        return ControlButton(icon=icon, name=name, click=change_drawer_ui)
