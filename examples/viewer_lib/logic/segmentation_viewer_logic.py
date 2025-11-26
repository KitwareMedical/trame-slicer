from dataclasses import dataclass

from trame_server import Server

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories

from ..ui import SegmentationViewerUI, StateId
from .base_logic import BaseLogic
from .layout_button_logic import LayoutButtonLogic
from .load_files_logic import LoadFilesLogic
from .segmentation import SegmentEditorLogic


@dataclass
class SegmentationViewerState:
    pass


class SegmentationViewerLogic(BaseLogic[SegmentationViewerState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentationViewerState)

        # Register the RCA view creation
        register_rca_factories(self._slicer_app.view_manager, self._server)

        # Create the application logic
        self._segment_editor_logic = SegmentEditorLogic(server, slicer_app)
        self._layout_button_logic = LayoutButtonLogic(server, slicer_app)
        self._load_files_logic = LoadFilesLogic(server, slicer_app)

        # Initialize the state defaults
        self.server.state.setdefault(StateId.vr_preset_value, "CT-Coronary-Arteries-3")
        self.server.state["trame__title"] = "trame Slicer"
        self.server.state["trame__favicon"] = (
            "https://raw.githubusercontent.com/Slicer/Slicer/main/Applications/SlicerApp/Resources/Icons/Medium/Slicer-DesktopIcon.png"
        )

    @property
    def layout_manager(self) -> LayoutManager:
        return self._layout_button_logic.layout_manager

    def set_ui(self, ui: SegmentationViewerUI):
        self._segment_editor_logic.set_ui(ui.segment_editor_ui)
        self._layout_button_logic.set_ui(ui.layout_button)
        self._load_files_logic.set_ui(ui.load_client_volume_items_buttons)
