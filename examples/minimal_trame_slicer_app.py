"""
Minimal example of starting a trame-slicer server for testing and demonstration purpose.

Doesn't provide any real features and only creates the minimum required components to create a trame-slicer application.
"""

from trame.app import TrameApp
from trame_vuetify.ui.vuetify3 import SinglePageLayout

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories


class MinimalTrameSlicerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server)

        # Slicer application creation
        self._slicer_app = SlicerApp()

        # Remote controlled view factory registration
        register_rca_factories(
            self._slicer_app.view_manager,
            self._server,
        )

        # Layout creation and view layout registration
        self._layout_manager = LayoutManager(
            self._slicer_app.scene,
            self._slicer_app.view_manager,
            self._server.ui.layout_grid,
        )

        # Register a layout and set the default view layout
        self._layout_manager.register_layout_dict(
            LayoutManager.default_grid_configuration(),
        )
        self._layout_manager.set_layout("Axial Primary")

        # Build the trame UI and populate the layout place-holder
        with SinglePageLayout(self._server) as self.ui, self.ui.content:
            self._layout_manager.initialize_layout_grid(self.ui)


if __name__ == "__main__":
    app = MinimalTrameSlicerApp()
    app.server.start()
