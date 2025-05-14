from __future__ import annotations

from trame.decorators import TrameApp, change
from trame_client.widgets.core import Template
from trame_server import Server
from trame_vuetify.widgets.vuetify3 import VCard, VCardText, VMenu, VRadio, VRadioGroup

from trame_slicer.core import LayoutManager, SlicerApp

from .control_button import ControlButton
from .utils import StateId


@TrameApp()
class LayoutButton(VMenu):
    def __init__(
        self,
        server: Server,
        slicer_app: SlicerApp,
        layout_manager: LayoutManager,
    ):
        super().__init__(location="right", close_on_content_click=True)
        self._server = server
        self._slicer_app = slicer_app
        self._layout_manager = layout_manager
        self._build_ui()

    def _build_ui(self):
        with self:
            with Template(v_slot_activator="{props}"):
                ControlButton(
                    v_bind="props",
                    icon="mdi-view-dashboard",
                    name="Layouts",
                )

            with (
                VCard(),
                VCardText(),
                VRadioGroup(
                    v_model=StateId.current_layout_name,
                    classes="mt-0",
                    hide_details=True,
                ),
            ):
                for layout in self._layout_manager.get_layout_ids():
                    VRadio(label=layout, value=layout)

    @change(StateId.current_layout_name)
    def on_current_layout_changed(self, **kwargs):
        self._layout_manager.set_layout(kwargs[StateId.current_layout_name])
