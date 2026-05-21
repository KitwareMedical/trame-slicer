from trame_server import Server

from trame_slicer.core import LayoutManager, SlicerApp

from ..ui import LayoutButtonState
from .base_logic import BaseLogic


class LayoutButtonLogic(BaseLogic[LayoutButtonState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, LayoutButtonState)

        self._layout_manager = LayoutManager(self._slicer_app.scene, self._slicer_app.view_manager, self._server)
        self._layout_manager.registered_layouts_changed.connect(self._refresh_layouts)
        self._layout_manager.register_layout_dict(LayoutManager.default_grid_configuration())

        self.bind_changes({self.name.current_layout_id: self._on_current_layout_changed})
        self._refresh_layouts()
        self._on_current_layout_changed(self.data.current_layout_id)

    def _on_current_layout_changed(self, layout_id: str):
        self._layout_manager.set_layout(layout_id)

    def _refresh_layouts(self):
        self.data.layout_ids = self._layout_manager.get_layout_ids()

    @property
    def layout_manager(self) -> LayoutManager:
        return self._layout_manager
