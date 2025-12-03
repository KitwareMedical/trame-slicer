from trame_server import Server

from trame_slicer.core import LayoutManager, SlicerApp

from .flex_container import FlexContainer
from .layout_button import LayoutButton
from .load_volume_ui import LoadVolumeDiv
from .markups_button import MarkupsButton
from .mpr_interaction_button import MprInteractionButton
from .segmentation import SegmentEditorUI
from .slab_button import SlabButton
from .viewer_layout import ViewerLayout
from .volume_property_button import VolumePropertyButton


class MedicalViewerUI:
    def __init__(self, server: Server, slicer_app: SlicerApp, layout_manager: LayoutManager):
        with ViewerLayout(server) as self.layout:
            self.segment_editor_ui = SegmentEditorUI()
            with self.layout.toolbar, FlexContainer(fill_height=True):
                self.load_volume_buttons = LoadVolumeDiv()
                self.volume_property_button = VolumePropertyButton(server=server, slicer_app=slicer_app)
                self.layout_button = LayoutButton()
                self.markups_button = MarkupsButton()
                self.segment_editor_ui.build_activator(click=self.activate_tool)
                self.slab_button = SlabButton()
                self.mpr_interaction_button = MprInteractionButton()

                self.segment_editor_ui.build_toolbar_ui()

            with self.layout.drawer:
                self.segment_editor_ui.build_drawer_ui()

            with self.layout.content, FlexContainer(row=True, fill_height=True):
                layout_manager.initialize_layout_grid(self.layout)

    @property
    def data(self):
        return self.layout.typed_state.data

    @property
    def name(self):
        return self.layout.typed_state.name

    def activate_tool(self, tool_name):
        if self.data.is_drawer_visible and self.data.active_tool == tool_name:
            self.data.is_drawer_visible = False
            self.data.active_tool = None
        else:
            self.data.active_tool = tool_name
            self.data.is_drawer_visible = True
