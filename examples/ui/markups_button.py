from trame_client.widgets.core import Template
from trame_client.widgets.html import Div
from trame_vuetify.widgets.vuetify3 import VCard, VCardText, VMenu, VRow
from undo_stack import Signal

from .control_button import ControlButton


class MarkupsButton(VMenu):
    place_node_type = Signal(str, bool)
    clear_clicked = Signal()

    def __init__(self):
        super().__init__(location="end", close_on_content_click=True)
        self._markup_nodes = []

        with self:
            with Template(v_slot_activator="{ props }"):
                ControlButton(name="Markups", icon="mdi-dots-square", v_bind="props")

            with VCard(), VCardText(), VRow(), Div(classes="d-flex flex-column"):
                self._create_markups_button(
                    name="Place points",
                    icon="mdi-circle-small",
                    node_type="vtkMRMLMarkupsFiducialNode",
                    is_persistent=True,
                )

                self._create_markups_button(
                    name="Place ruler",
                    icon="mdi-ruler",
                    node_type="vtkMRMLMarkupsLineNode",
                    is_persistent=False,
                )

                self._create_markups_button(
                    name="Place angle measurement",
                    icon="mdi-angle-acute",
                    node_type="vtkMRMLMarkupsAngleNode",
                    is_persistent=False,
                )

                self._create_markups_button(
                    name="Place open curve",
                    icon="mdi-vector-polyline",
                    node_type="vtkMRMLMarkupsCurveNode",
                    is_persistent=True,
                )

                self._create_markups_button(
                    name="Place closed curve",
                    icon="mdi-vector-polygon",
                    node_type="vtkMRMLMarkupsClosedCurveNode",
                    is_persistent=True,
                )

                self._create_markups_button(
                    name="Place plane",
                    icon="mdi-square-outline",
                    node_type="vtkMRMLMarkupsPlaneNode",
                    is_persistent=False,
                )

                self._create_markups_button(
                    name="Place ROI",
                    icon="mdi-cube-outline",
                    node_type="vtkMRMLMarkupsROINode",
                    is_persistent=False,
                )

                ControlButton(
                    name="Clear Markups",
                    icon="mdi-trash-can-outline",
                    click=self.clear_clicked,
                )

    def _create_markups_button(self, name: str, icon: str, node_type: str, is_persistent: bool) -> None:
        def on_click():
            self.place_node_type(node_type, is_persistent)

        ControlButton(name=name, icon=icon, click=on_click)
