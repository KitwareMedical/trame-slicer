from trame_server import Server

from examples.ui import SlabState, SlabType
from trame_slicer.core import SlicerApp

from .base_logic import BaseLogic


class SlabLogic(BaseLogic[SlabState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SlabState)
        self.bind_changes(
            {
                self.name.current_slab_type: self.on_current_slab_type_change,
                self.name.slab_enabled: self._on_slab_toggled,
                self.name.slab_thickness_value: self.on_slab_slider_change,
            }
        )

    def on_slab_slider_change(self, slab_thickness: float):
        for slice_view in self._slicer_app.view_manager.get_slice_views():
            slice_view.set_slab_thickness(slab_thickness)

    def on_current_slab_type_change(self, current_slab_type: SlabType):
        for slice_view in self._slicer_app.view_manager.get_slice_views():
            slice_view.set_slab_type(current_slab_type.value)

    def _on_slab_toggled(self, is_enabled: bool):
        for slice_view in self._slicer_app.view_manager.get_slice_views():
            slice_view.set_slab_enabled(is_enabled)
