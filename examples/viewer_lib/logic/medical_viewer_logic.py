from dataclasses import dataclass

from trame_server import Server

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories

from ..ui import MedicalViewerUI, StateId
from .base_logic import BaseLogic
from .layout_button_logic import LayoutButtonLogic
from .load_files_logic import LoadFilesLogic
from .markups_button_logic import MarkupsButtonLogic
from .mpr_interaction_button_logic import MprInteractionButtonLogic
from .segmentation import SegmentEditorLogic
from .slab_logic import SlabLogic


@dataclass
class MedicalViewerState:
    pass


class MedicalViewerLogic(BaseLogic[MedicalViewerState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, MedicalViewerState)

        # Register the RCA view creation
        register_rca_factories(self._slicer_app.view_manager, self._server)

        # Create the application logic
        self._segment_editor_logic = SegmentEditorLogic(server, slicer_app)
        self._layout_button_logic = LayoutButtonLogic(server, slicer_app)
        self._markups_logic = MarkupsButtonLogic(server, slicer_app)
        self._load_files_logic = LoadFilesLogic(server, slicer_app)
        self._slab_logic = SlabLogic(server, slicer_app)
        self._mpr_logic = MprInteractionButtonLogic(server, slicer_app)

        # Initialize the state defaults
        self.server.state.setdefault(StateId.vr_preset_value, "CT-Coronary-Arteries-3")
        self.server.state["trame__title"] = "trame Slicer"
        self.server.state["trame__favicon"] = (
            "https://raw.githubusercontent.com/Slicer/Slicer/main/Applications/SlicerApp/Resources/Icons/Medium/Slicer-DesktopIcon.png"
        )

    @property
    def layout_manager(self) -> LayoutManager:
        return self._layout_button_logic.layout_manager

    def set_ui(self, ui: MedicalViewerUI):
        self._segment_editor_logic.set_ui(ui.segment_editor_ui)
        self._layout_button_logic.set_ui(ui.layout_button)
        self._markups_logic.set_ui(ui.markups_button)
        self._load_files_logic.set_ui(ui.load_client_volume_files_button)
        self._slab_logic.set_ui(ui.slab_button)
        self._mpr_logic.set_ui(ui.mpr_interaction_button)
