from slicer import vtkMRMLVolumeNode
from trame_server import Server

from trame_slicer.core import SlicerApp, VolumeWindowLevel
from trame_slicer.resources import get_volume_rendering_presets_icon_url

from ..ui import Preset, VolumePropertyState, VolumePropertyUI
from .base_logic import BaseLogic


class VolumePropertyLogic(BaseLogic[VolumePropertyState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, VolumePropertyState)
        self._volume_node = None
        self._populate_presets()

        self._typed_state.bind_changes(
            {
                self.name.vr_shift_slider.value: self._set_vr_shift_value,
                self.name.window_level_slider.value: self._set_window_level_value,
                self.name.preset_name: self._set_preset,
            }
        )

    def set_ui(self, ui: VolumePropertyUI):
        ui.auto_window_level_clicked.connect(self._auto_window_level)
        ui.vr_crop_button_clicked.connect(self._toggle_vr_crop)

    @property
    def _volume_rendering(self):
        return self._slicer_app.volume_rendering

    def _populate_presets(self):
        presets = [
            Preset(title=name, props={"data": data})
            for name, data in get_volume_rendering_presets_icon_url(
                icons_folder=(self._slicer_app.share_directory / "presets_icons"),
                volume_rendering=self._volume_rendering,
            )
        ]

        self.data.presets = presets

    def on_volume_changed(self, volume_node: vtkMRMLVolumeNode):
        self._volume_node = volume_node

        self._init_preset()
        self._init_window_level_slider()

    def _init_preset(self):
        self._set_preset(self.data.preset_name)

    def _auto_window_level(self):
        if not self._volume_node:
            return

        self.data.window_level_slider.value = list(VolumeWindowLevel.get_volume_auto_min_max_range(self._volume_node))

    def _toggle_vr_crop(self):
        was_active = self._typed_state.data.volume_crop_active
        if not self._volume_node:
            return

        display_node = self._volume_rendering.get_vr_display_node(self._volume_node)
        roi_node = display_node.GetROINode()

        roi_node = self._volume_rendering.set_cropping_enabled(self._volume_node, roi_node, True)
        is_active = not was_active
        roi_node.SetDisplayVisibility(is_active)
        self.data.volume_crop_active = is_active

    def _init_window_level_slider(self):
        if not self._volume_node:
            return

        min_value, max_value = VolumeWindowLevel.get_volume_scalar_range(self._volume_node)
        self.data.window_level_slider.min_value = min_value
        self.data.window_level_slider.max_value = max_value
        self._auto_window_level()

    def _init_vr_shift_slider(self):
        self.data.vr_shift_slider.min_value, self.data.vr_shift_slider.max_value = (
            self._volume_rendering.get_preset_vr_shift_range(self.data.preset_name)
        )
        self.data.vr_shift_slider.value = 0

    def _set_preset(self, preset_name: str):
        if not self._volume_node:
            return

        vr_node = self._volume_rendering.get_vr_display_node(self._volume_node)
        self._volume_rendering.apply_preset(vr_node, preset_name)
        self._init_vr_shift_slider()

    def _set_window_level_value(self, window_level: list[float]):
        if not self._volume_node:
            return

        min_value, max_value = window_level
        VolumeWindowLevel.set_volume_node_display_min_max_range(self._volume_node, min_value, max_value)

    def _set_vr_shift_value(self, vr_shift_value: float):
        if not self._volume_node:
            return

        self._volume_rendering.set_absolute_vr_shift_from_preset(
            self._volume_node,
            self.data.preset_name,
            vr_shift_value,
        )
