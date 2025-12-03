from trame_server import Server

from trame_slicer.core import SlicerApp

from ...ui import SegmentEditState, SegmentEditUI
from .base_segmentation_logic import BaseSegmentationLogic


class SegmentEditLogic(BaseSegmentationLogic[SegmentEditState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentEditState)

    def set_ui(self, ui: SegmentEditUI):
        ui.name_edited.connect(self._save_segment_values)
        ui.validate_color_clicked.connect(self._on_color_validate)
        ui.cancel_clicked.connect(self._hide_color_dialog)

    def _save_segment_values(self):
        segment_properties = self.segmentation_editor.get_segment_properties(self.data.segment_state.segment_id)
        if not segment_properties:
            return

        segment_properties.name = self.data.segment_state.name
        segment_properties.color_hex = self.data.segment_state.color
        self.segmentation_editor.set_segment_properties(self.data.segment_state.segment_id, segment_properties)

    def _on_color_validate(self):
        try:
            self._save_segment_values()
        finally:
            self._hide_color_dialog()

    def set_segment_edit_values(self, segment_id: str):
        segment_properties = self.segmentation_editor.get_segment_properties(segment_id)
        if segment_properties is None:
            return

        self.data.segment_state.name = segment_properties.name
        self.data.segment_state.color = segment_properties.color_hex
        self.data.segment_state.segment_id = segment_id

    def _set_color_dialog_visible(self, is_visible: bool):
        self.data.is_color_dialog_visible = is_visible

    def show_color_dialog(self):
        self._set_color_dialog_visible(True)

    def _hide_color_dialog(self):
        self._set_color_dialog_visible(False)
