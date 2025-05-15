from __future__ import annotations

from trame.decorators import TrameApp, change
from trame_client.widgets.core import Template
from trame_client.widgets.html import Span
from trame_server import Server
from trame_vuetify.widgets.vuetify3 import VImg, VListItem, VSelect

from trame_slicer.core import SlicerApp
from trame_slicer.resources import get_volume_rendering_presets_icon_url

from .utils import StateId, get_current_volume_node


@TrameApp()
class VRPresetSelect(VSelect):
    """
    Volume rendering select component.
    Allows to select and change the presets of the current volume loaded in the scene.
    """

    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(
            items=(StateId.vr_presets,),
            v_model=(StateId.vr_preset_value,),
            hide_details=True,
        )
        self._server = server
        self._slicer_app = slicer_app
        self._populate_presets()

        with self:
            with (
                Template(v_slot_item="{props}"),
                VListItem(v_bind="props"),
                Template(v_slot_prepend=""),
                Span(classes="pr-2"),
            ):
                VImg(src=("props.data",), height=64, width=64)

            with Template(v_slot_selection="{item}"):
                VImg(src=("item.props.data",), height=32, width=32)
                Span("{{item.title}}", classes="pl-2")

    def _populate_presets(self):
        presets = [
            {"title": name, "props": {"data": data}}
            for name, data in get_volume_rendering_presets_icon_url(
                icons_folder=(self._slicer_app.share_directory / "presets_icons"),
                volume_rendering=self._volume_rendering,
            )
        ]

        self.state.setdefault(StateId.vr_presets, presets)

    @property
    def _volume_rendering(self):
        return self._slicer_app.volume_rendering

    @change(StateId.vr_preset_value)
    def on_vr_preset_change(self, **kwargs):
        vr_node = self._volume_rendering.get_vr_display_node(get_current_volume_node(self.server, self._slicer_app))
        preset_name = kwargs[StateId.vr_preset_value]
        self._volume_rendering.apply_preset(vr_node, preset_name)
        self._update_vr_range(preset_name)
        self.state[StateId.vr_slider_value] = 0

    def _update_vr_range(self, preset_name):
        self.state[StateId.vr_slider_min], self.state[StateId.vr_slider_max] = (
            self._volume_rendering.get_preset_vr_shift_range(preset_name)
        )
