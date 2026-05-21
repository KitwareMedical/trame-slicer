from trame.widgets.vuetify3 import Template
from trame_server import Server

from trame_slicer.core import LayoutManager

from .control_button import ControlButton
from .layout_button import LayoutButton
from .load_volume_ui import LoadVolumeUI
from .mpr_interaction_button import MprInteractionButton
from .segmentation import (
    SegmentEditorToolbarUI,
    SegmentEditorUI,
    SegmentEditorUndoRedoUI,
)
from .viewer_layout import ViewerLayout
from .volume_property_ui import VolumePropertyUI


class SegmentationAppUI:
    def __init__(self, server: Server, layout_manager: LayoutManager):
        self.tool_registry = {}

        with ViewerLayout(server) as self.layout:
            self.layout.title.set_text("Segmentation App")
            with self.layout.appbar, Template(v_slot_prepend=True):
                self.load_volume_items_buttons = LoadVolumeUI()

            with self.layout.drawer:
                self._register_tool_ui(SegmentEditorUI)
                self._register_tool_ui(VolumePropertyUI)

            with self.layout.toolbar:
                self._create_tool_button(
                    icon="mdi-tune-variant",
                    name="Volume Properties",
                    tool_ui_type=VolumePropertyUI,
                )
                self.layout_button = LayoutButton(classes="mt-1", disabled=(f"!{self.name.is_volume_loaded}",))
                self.mpr_interaction_button = MprInteractionButton(
                    classes="mt-1", disabled=(f"!{self.name.is_volume_loaded}",)
                )
                self._create_tool_button(
                    icon="mdi-brush",
                    name="segmentation panel",
                    tool_ui_type=SegmentEditorUI,
                )
                self._register_toolbar_ui(SegmentEditorToolbarUI, SegmentEditorUI)

            with self.layout.undo_redo:
                self._register_undo_redo_ui(SegmentEditorUndoRedoUI, SegmentEditorUI)

            with self.layout.content:
                layout_manager.initialize_layout_grid(self.layout)

    @property
    def data(self):
        return self.layout.typed_state.data

    @property
    def name(self):
        return self.layout.typed_state.name

    def _is_tool_active(self, tool_ui_type: type):
        return f"{self.name.active_tool} === '{tool_ui_type.__name__}'"

    def _is_tool_drawer_visible(self, tool_ui_type: type):
        return f"{self._is_tool_active(tool_ui_type)} && {self.name.is_drawer_visible}"

    def _register_tool_ui(self, tool_ui_type: type, **kwargs):
        tool_instance = tool_ui_type(v_if=(self._is_tool_active(tool_ui_type),), **kwargs)
        self.tool_registry[tool_ui_type] = tool_instance

    def _register_toolbar_ui(self, toolbar_ui_type: type, tool_ui_type: type):
        toolbar_ui_type(editor_ui=self.tool_registry[tool_ui_type])

    def _register_undo_redo_ui(self, undo_redo_ui_type: type, tool_ui_type: type):
        undo_redo_ui_type(
            editor_ui=self.tool_registry[tool_ui_type],
            v_if=(self._is_tool_active(tool_ui_type),),
        )

    def _create_tool_button(self, name: str, icon: str | tuple, tool_ui_type: type):
        async def change_drawer_ui():
            is_drawer_visible = not self.data.is_drawer_visible or self.data.active_tool != tool_ui_type.__name__
            self.data.is_drawer_visible = is_drawer_visible
            self.data.active_tool = tool_ui_type.__name__ if is_drawer_visible else None

        return ControlButton(
            icon=icon,
            name="{{ " + f"{self._is_tool_drawer_visible(tool_ui_type)} ? 'Close {name}' : 'Open {name}'" + " }}",
            click=change_drawer_ui,
            active=(self._is_tool_active(tool_ui_type),),
            disabled=(f"!{self.name.is_volume_loaded}",),
            classes="mt-1",
        )
