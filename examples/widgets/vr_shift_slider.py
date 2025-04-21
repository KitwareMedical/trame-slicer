from trame.decorators import TrameApp, change
from trame_server import Server
from trame_vuetify.widgets.vuetify3 import VSlider

from trame_slicer.core import SlicerApp

from .utils import StateId, get_current_volume_node


@TrameApp()
class VRShiftSlider(VSlider):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(
            v_model=(StateId.vr_slider_value,),
            min=(StateId.vr_slider_min,),
            max=(StateId.vr_slider_max,),
            width=250,
            hide_details=True,
        )
        self._server = server
        self._slicer_app = slicer_app

    @property
    def _volume_rendering(self):
        return self._slicer_app.volume_rendering

    @change(StateId.vr_slider_value)
    def on_vr_slider_change(self, **kwargs):
        volume_node = get_current_volume_node(self.server, self._slicer_app)
        self._volume_rendering.set_absolute_vr_shift_from_preset(
            volume_node,
            kwargs[StateId.vr_preset_value],
            kwargs[StateId.vr_slider_value],
        )
