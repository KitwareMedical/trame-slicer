from trame_server import Server

from trame_slicer.core import SlicerApp

from ...ui import SegmentEditUI, SegmentState
from .base_segmentation_logic import BaseSegmentationLogic


class SegmentEditLogic(BaseSegmentationLogic[SegmentState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentState)
        self._ui = None

    def set_ui(self, ui: SegmentEditUI):
        self._ui = ui
        self._ui.name_changed.connect(self._save_segment_values)
        self._ui.color_changed.connect(self._on_color_changed)
        self._ui.cancel_clicked.connect(self._hide_color_dialog)

    def _save_segment_values(self):
        segment_properties = self.segmentation_editor.get_segment_properties(self.data.segment_id)
        if not segment_properties:
            return

        segment_properties.name = self.data.name
        segment_properties.color_hex = self.data.color
        self.segmentation_editor.set_segment_properties(self.data.segment_id, segment_properties)

    def _on_color_changed(self):
        try:
            self.data.color = self._ui.color_dialog.get_color()
            self._save_segment_values()
        finally:
            self._hide_color_dialog()

    def set_active_segment_id(self, segment_id: str):
        segment_properties = self.segmentation_editor.get_segment_properties(segment_id)

        self.data.name = "" if segment_properties is None else segment_properties.name
        self.data.color = "" if segment_properties is None else segment_properties.color_hex
        self.data.segment_id = segment_id

    def show_color_dialog(self):
        if self._ui is not None:
            self._ui.color_dialog.set_color(self.data.color)
            self._ui.color_dialog.open()

    def _hide_color_dialog(self):
        if self._ui is not None:
            self._ui.color_dialog.close()
