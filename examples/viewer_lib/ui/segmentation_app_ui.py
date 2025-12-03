from trame_server import Server

from trame_slicer.core import LayoutManager

from .flex_container import FlexContainer
from .layout_button import LayoutButton
from .load_volume_ui import LoadVolumeDiv
from .segmentation import SegmentEditorUI
from .viewer_layout import ViewerLayout


class SegmentationAppUI:
    def __init__(self, server: Server, layout_manager: LayoutManager):
        with ViewerLayout(server) as self.layout:
            self.segment_editor_ui = SegmentEditorUI()
            with self.layout.toolbar, FlexContainer(fill_height=True):
                self.load_volume_items_buttons = LoadVolumeDiv()
                self.layout_button = LayoutButton()
                self.segment_editor_ui.build_activator(click=self.activate_tool)
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
        else:
            self.data.active_tool = tool_name
            self.data.is_drawer_visible = True
