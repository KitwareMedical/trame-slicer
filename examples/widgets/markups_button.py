from __future__ import annotations

from slicer import vtkMRMLMarkupsNode
from trame_client.widgets.core import Template
from trame_client.widgets.html import Div
from trame_server import Server
from trame_vuetify.widgets.vuetify3 import VCard, VCardText, VMenu, VRow

from trame_slicer.core import SlicerApp
from trame_slicer.core.markups_logic import MarkupsLogic

from .control_button import ControlButton


class MarkupsButton(VMenu):
    """
    Represents a customizable button interface for creating and managing markups within
    a slicer's application environment, with specific interaction controls such as
    placing points, rulers, angles, curves, planes, and regions of interest (ROI). This
    class also allows clearing of created markups.

    The `MarkupsButton` is designed to provide a variety of actions related to markup
    nodes within a visualization tool, encapsulating both the UI components and their
    functionality.
    """

    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(location="end", close_on_content_click=True)
        self._slicer_app = slicer_app
        self._server = server
        self._markup_nodes = []

        with self:
            with Template(v_slot_activator="{ props }"):
                ControlButton(name="Markups", icon="mdi-dots-square", v_bind="props")

            with VCard(), VCardText(), VRow(), Div(classes="d-flex flex-column"):
                self.create_markups_button(
                    name="Place points",
                    icon="mdi-circle-small",
                    node_type="vtkMRMLMarkupsFiducialNode",
                    is_persistent=True,
                )

                self.create_markups_button(
                    name="Place ruler",
                    icon="mdi-ruler",
                    node_type="vtkMRMLMarkupsLineNode",
                    is_persistent=False,
                )

                self.create_markups_button(
                    name="Place angle measurement",
                    icon="mdi-angle-acute",
                    node_type="vtkMRMLMarkupsAngleNode",
                    is_persistent=False,
                )

                self.create_markups_button(
                    name="Place open curve",
                    icon="mdi-vector-polyline",
                    node_type="vtkMRMLMarkupsCurveNode",
                    is_persistent=True,
                )

                self.create_markups_button(
                    name="Place closed curve",
                    icon="mdi-vector-polygon",
                    node_type="vtkMRMLMarkupsClosedCurveNode",
                    is_persistent=True,
                )

                self.create_markups_button(
                    name="Place plane",
                    icon="mdi-square-outline",
                    node_type="vtkMRMLMarkupsPlaneNode",
                    is_persistent=False,
                )

                self.create_markups_button(
                    name="Place ROI",
                    icon="mdi-cube-outline",
                    node_type="vtkMRMLMarkupsROINode",
                    is_persistent=False,
                )

                ControlButton(
                    name="Clear Markups",
                    icon="mdi-trash-can-outline",
                    click=self.on_clear_clicked,
                )

    @property
    def markups_logic(self) -> MarkupsLogic:
        return self._slicer_app.markups_logic

    def create_markups_button(self, name: str, icon: str, node_type: str, is_persistent: bool) -> None:
        """
        Creates a button to place a specific node type in a persistent or temporary
        manner. This function generates a clickable button using the given name,
        icon, node type, and persistence setting. When the button is clicked,
        it triggers the associated callback logic to set a node type in the system.

        :param name: The display name of the button.
        :param icon: The path or identifier for the button's graphical icon.
        :param node_type: The type of the node that the button is responsible for assigning.
        :param is_persistent: Defines whether the node type placement is persistent or not.
        """

        def on_click():
            self.place_node_type(node_type, is_persistent=is_persistent)

        ControlButton(name=name, icon=icon, click=on_click)

    def on_clear_clicked(self) -> None:
        """
        Handles the clear button click event to remove all markup nodes from the
        scene. This method iterates through a list of markup nodes and removes
        each node from the application's scene.
        """
        for node in self._markup_nodes:
            self._slicer_app.scene.RemoveNode(node)

    def create_node(self, node_type: str) -> vtkMRMLMarkupsNode:
        """
        Creates a new node in the scene of the specified type and appends it to the list
        of markup nodes if successfully created.

        :param node_type: The type of node to be created as a string.
        :return: The newly created node of type vtkMRMLMarkupsNode.
        """
        node = self._slicer_app.scene.AddNewNodeByClass(node_type)
        if node:
            self._markup_nodes.append(node)
        return node

    def place_node_type(self, node_type: str, is_persistent: bool) -> None:
        """
        Places a node of the specified type into the system and manages its persistence.
        This function creates a new node of the given type and uses the logic
        to position the node correctly while determining its persistent state.

        :param node_type: The type of the node to be created.
        :param is_persistent: Indicates whether the node should persist in the system.
        :return: None
        """
        node = self.create_node(node_type)
        if node is not None:
            self.markups_logic.place_node(node, is_persistent)
