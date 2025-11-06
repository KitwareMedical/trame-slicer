from trame_server import Server

from examples.ui import SegmentEditDialog, SegmentEditDialogState, SegmentEditorUI
from trame_slicer.core import SlicerApp

from .base_segmentation_logic import BaseSegmentationLogic


class SegmentEditDialogLogic(BaseSegmentationLogic[SegmentEditDialogState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentEditDialogState)

    def set_ui(self, ui: SegmentEditorUI):
        self.set_edit_dialog(ui.edit_dialog)

    def set_edit_dialog(self, edit_dialog: SegmentEditDialog):
        edit_dialog.validate_clicked.connect(self._on_validate)
        edit_dialog.cancel_clicked.connect(self._hide_dialog)

    def _on_validate(self):
        try:
            segment_properties = self.segmentation_editor.get_segment_properties(self.data.segment_state.segment_id)
            if not segment_properties:
                return

            segment_properties.name = self.data.segment_state.name
            segment_properties.color_hex = self.data.segment_state.color
            self.segmentation_editor.set_segment_properties(self.data.segment_state.segment_id, segment_properties)
        finally:
            self._hide_dialog()

    def show_dialog(self, segment_id: str):
        segment_properties = self.segmentation_editor.get_segment_properties(segment_id)
        if segment_properties is None:
            return

        self.data.segment_state.name = segment_properties.name
        self.data.segment_state.color = segment_properties.color_hex
        self.data.segment_state.segment_id = segment_id
        self.data.is_visible = True

    def _hide_dialog(self):
        self.data.is_visible = False
