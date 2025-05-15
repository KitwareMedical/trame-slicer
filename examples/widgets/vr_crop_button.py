from __future__ import annotations

from trame.decorators import TrameApp
from trame_client.widgets.html import Div
from trame_server import Server

from trame_slicer.core import SlicerApp

from .control_button import ControlButton
from .utils import IdName, get_current_volume_node


@TrameApp()
class VRCropButton(Div):
    """
    Responsible for controlling the Volume Rendering crop of the current volume node.
    """

    volume_crop_active = IdName()

    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(classes="d-flex flex-row")
        server.state.setdefault(self.volume_crop_active, False)
        self._volume_rendering = slicer_app.volume_rendering
        self._slicer_app = slicer_app

        with self:
            ControlButton(
                icon="mdi-crop",
                name="Crop volume rendering",
                active=(self.volume_crop_active,),
                click=self._on_crop_toggled,
                size=32,
            )
            Div("VR Crop", style="align-self: center;")

    def _on_crop_toggled(self):
        was_active = self.state[self.volume_crop_active]
        volume_node = get_current_volume_node(self.server, self._slicer_app)
        if not volume_node:
            return

        display_node = self._volume_rendering.get_vr_display_node(volume_node)
        roi_node = display_node.GetROINode()

        roi_node = self._volume_rendering.set_cropping_enabled(volume_node, roi_node, True)
        is_active = not was_active
        roi_node.SetDisplayVisibility(is_active)
        self.state[self.volume_crop_active] = is_active
