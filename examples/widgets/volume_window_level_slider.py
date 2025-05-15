from __future__ import annotations

from trame.decorators import TrameApp, change
from trame_client.widgets.html import Div
from trame_server import Server
from trame_vuetify.widgets.vuetify3 import VRangeSlider

from trame_slicer.core import SlicerApp, VolumeWindowLevel

from .control_button import ControlButton
from .utils import IdName, StateId, get_current_volume_node


@TrameApp()
class VolumeWindowLevelSlider(Div):
    volume_display_range = IdName()
    volume_min_range = IdName()
    volume_max_range = IdName()

    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(classes="d-flex flex-row")
        self._server = server
        self._slicer_app = slicer_app
        self._volume_node = None

        @self.server.state.change(self.volume_display_range)
        def display_changed(**_):
            self.on_display_changed()

        with self:
            ControlButton(
                name="Auto Window/Level",
                icon="mdi-refresh-auto",
                click=self.on_auto_window_level,
                size=32,
            )
            VRangeSlider(
                min=(self.volume_min_range, 0),
                max=(self.volume_max_range, 100),
                v_model=(self.volume_display_range, [20, 40]),
                hide_details=True,
                width=250,
            )

    @change(StateId.current_volume_node_id)
    def on_volume_changed(self, **_):
        self._volume_node = get_current_volume_node(self._server, self._slicer_app)
        if not self._volume_node:
            return

        min_value, max_value = VolumeWindowLevel.get_volume_scalar_range(self._volume_node)
        self.state[self.volume_min_range] = min_value
        self.state[self.volume_max_range] = max_value
        self.on_auto_window_level()

    def on_display_changed(self):
        if not self._volume_node:
            return

        min_value, max_value = self.state[self.volume_display_range]
        VolumeWindowLevel.set_volume_node_display_min_max_range(self._volume_node, min_value, max_value)

    def on_auto_window_level(self):
        if not self._volume_node:
            return

        self.state[self.volume_display_range] = list(VolumeWindowLevel.get_volume_auto_min_max_range(self._volume_node))
