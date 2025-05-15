from __future__ import annotations

from trame.app import get_server
from trame.app.testing import enable_testing
from trame.decorators import TrameApp
from trame.widgets import vuetify3
from trame_client.widgets.html import Div
from trame_server import Server
from trame_vuetify.ui.vuetify3 import SinglePageLayout
from widgets import StateId, ToolsStrip

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories


@TrameApp()
class MyTrameSlicerApp:
    def __init__(self, server=None):
        self._server = get_server(server, client_type="vue3")
        self._slicer_app = SlicerApp()

        # Register the RCA view creation
        # The registration needs to happen before the UI is populated
        register_rca_factories(self._slicer_app.view_manager, self._server)

        # Create the trame layout manager and initialize it with the default grid configuration
        self._layout_manager = LayoutManager(
            self._slicer_app.scene,
            self._slicer_app.view_manager,
            self._server.ui.layout_grid,
        )

        self._layout_manager.register_layout_dict(LayoutManager.default_grid_configuration())

        # Build the trame UI with the widgets available in the widget package
        self._build_ui()

        # Initialize the state defaults
        self.server.state.setdefault(
            StateId.vr_preset_value,
            "CT-Coronary-Arteries-3",
        )
        default_layout = "Axial Primary"
        self.server.state.setdefault(StateId.current_layout_name, default_layout)

        # Update the layout to the default layout
        self._layout_manager.set_layout(default_layout)

    @property
    def server(self) -> Server:
        return self._server

    def _build_ui(self):
        with SinglePageLayout(self._server) as self.ui:
            self.ui.root.theme = "dark"

            # Toolbar
            self.ui.title.set_text("trame Slicer")

            with self.ui.toolbar:
                vuetify3.VSpacer()

            # Main content
            with (
                self.ui.content,
                Div(classes="fill-height d-flex flex-row flex-grow-1"),
            ):
                ToolsStrip(
                    server=self._server,
                    slicer_app=self._slicer_app,
                    layout_manager=self._layout_manager,
                )
                self._server.ui.layout_grid(self.ui)


def main(server=None, **kwargs):
    app = MyTrameSlicerApp(server)
    enable_testing(app.server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
