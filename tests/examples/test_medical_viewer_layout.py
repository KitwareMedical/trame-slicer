from trame_vuetify.widgets.vuetify3 import VLabel, VSlider

from examples.viewer_lib.ui import ControlButton, ViewerLayout


def test_can_be_displayed(a_server, a_server_port):
    with ViewerLayout(a_server, is_drawer_visible=True) as ui:
        with ui.toolbar:
            ControlButton(name="Home", icon="mdi-home-circle")
            ControlButton(name="Cube tool", icon="mdi-cube-outline")

        with ui.drawer.clear():
            VLabel("Drawer content")
            VSlider()

    a_server.start(port=a_server_port)
