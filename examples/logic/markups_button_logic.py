from slicer import vtkMRMLMarkupsNode
from trame_server import Server

from examples.ui import MarkupsButton
from trame_slicer.core import SlicerApp

from .base_logic import BaseLogic


class MarkupsButtonLogic(BaseLogic):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, None)
        self._markup_nodes = []

    def set_ui(self, ui: MarkupsButton):
        ui.place_node_type.connect(self.on_place_node_type)
        ui.clear_clicked.connect(self.on_clear_clicked)

    def on_clear_clicked(self) -> None:
        for node in self._markup_nodes:
            self._slicer_app.scene.RemoveNode(node)

    def _create_node(self, node_type: str) -> vtkMRMLMarkupsNode:
        node = self._slicer_app.scene.AddNewNodeByClass(node_type)
        if node:
            self._markup_nodes.append(node)
        return node

    def on_place_node_type(self, node_type: str, is_persistent: bool) -> None:
        node = self._create_node(node_type)
        if node is not None:
            self._slicer_app.markups_logic.place_node(node, is_persistent)
