from trame_server import Server

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories

from ..ui import SegmentationAppUI, SegmentEditorUI, ViewerLayoutState, VolumePropertyUI
from .base_logic import BaseLogic
from .layout_button_logic import LayoutButtonLogic
from .load_volume_logic import LoadVolumeLogic
from .mpr_interaction_button_logic import MprInteractionButtonLogic
from .segmentation import SegmentEditorLogic
from .volume_property_logic import VolumePropertyLogic


class SegmentationAppLogic(BaseLogic[ViewerLayoutState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, ViewerLayoutState)

        # Register the RCA view creation
        register_rca_factories(self._slicer_app.view_manager, self._server)

        # Create the application logic
        self._segment_editor_logic = SegmentEditorLogic(server, slicer_app)
        self._volume_properties_logic = VolumePropertyLogic(server, slicer_app)
        self._layout_button_logic = LayoutButtonLogic(server, slicer_app)
        self._load_files_logic = LoadVolumeLogic(server, slicer_app)
        self._mpr_logic = MprInteractionButtonLogic(server, slicer_app)

        # Connect signals
        self._load_files_logic.volume_loaded.connect(self._on_volume_changed)
        self._load_files_logic.volume_loaded.connect(self._volume_properties_logic.on_volume_changed)
        self._load_files_logic.volume_loaded.connect(self._segment_editor_logic.on_volume_changed)

        # Initialize the state defaults
        self.server.state["trame__title"] = "trame Slicer"
        self.server.state["trame__favicon"] = (
            "https://raw.githubusercontent.com/Slicer/Slicer/main/Applications/SlicerApp/Resources/Icons/Medium/Slicer-DesktopIcon.png"
        )

    @property
    def layout_manager(self) -> LayoutManager:
        return self._layout_button_logic.layout_manager

    def set_ui(self, ui: SegmentationAppUI):
        self._segment_editor_logic.set_ui(ui.tool_registry[SegmentEditorUI])
        self._volume_properties_logic.set_ui(ui.tool_registry[VolumePropertyUI])
        self._layout_button_logic.set_ui(ui.layout_button)
        self._load_files_logic.set_ui(ui.load_volume_items_buttons)
        self._mpr_logic.set_ui(ui.mpr_interaction_button)

    def _on_volume_changed(self, *_args):
        self.data.is_drawer_visible = True
        self.data.active_tool = SegmentEditorUI.__name__
        self.data.is_volume_loaded = True
