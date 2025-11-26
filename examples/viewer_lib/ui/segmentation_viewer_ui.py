from trame_server import Server

from trame_slicer.core import LayoutManager

from .layout_button import LayoutButton
from .load_client_volume_files_button import LoadClientVolumeButtonsDiv
from .segmentation import SegmentEditorUI
from .utils import AbstractToolUI, ControlButton, FlexContainer
from .viewer_layout import ViewerLayout


class SegmentationViewerUI:
    def __init__(self, server: Server, layout_manager: LayoutManager):
        with ViewerLayout(server) as self.layout:
            self.segment_editor_ui = SegmentEditorUI()
            with self.layout.toolbar, FlexContainer(fill_height=True):
                self.load_client_volume_items_buttons = LoadClientVolumeButtonsDiv()
                self.layout_button = LayoutButton()
                self._create_tool_button(
                    icon="mdi-brush",
                    name="segmentation panel",
                    tool_name=self.segment_editor_ui.name,
                )
                self._register_toolbar_ui(self.segment_editor_ui)

            with self.layout.drawer:
                self._register_drawer_ui(self.segment_editor_ui)

            with self.layout.content, FlexContainer(row=True, fill_height=True):
                layout_manager.initialize_layout_grid(self.layout)

    @property
    def data(self):
        return self.layout.typed_state.data

    @property
    def name(self):
        return self.layout.typed_state.name

    def _register_toolbar_ui(self, tool: AbstractToolUI) -> None:
        tool.build_toolbar_ui(v_if=(self._is_tool_active(tool.name),))

    def _register_drawer_ui(self, tool: AbstractToolUI) -> None:
        tool.build_drawer_ui(v_if=(self._is_tool_drawer_visible(tool.name),))

    def _create_tool_button(self, name: str, icon: str | tuple, tool_name: type):
        async def change_drawer_ui():
            if self.data.is_drawer_visible and self.data.active_tool == tool_name:
                self.data.is_drawer_visible = False
            else:
                self.data.active_tool = tool_name
                self.data.is_drawer_visible = True

        ControlButton(
            icon=icon,
            name="{{ " + f"{self._is_tool_drawer_visible(tool_name)} ? 'Close {name}' : 'Open {name}'" + " }}",
            click=change_drawer_ui,
            active=(self._is_tool_active(tool_name),),
        )

    def _is_tool_active(self, tool_name):
        return f"{self.name.active_tool} === '{tool_name}'"

    def _is_tool_drawer_visible(self, tool_name):
        return f"{self._is_tool_active(tool_name)} && {self.name.is_drawer_visible}"
