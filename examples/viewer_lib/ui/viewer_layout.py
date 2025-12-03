from dataclasses import dataclass

from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets.vuetify3 import VNavigationDrawer
from trame_server import Server
from trame_server.utils.typed_state import TypedState


@dataclass
class ViewerLayoutState:
    is_drawer_visible: bool = False
    active_tool: str | None = None


class ViewerLayout(SinglePageLayout):
    def __init__(
        self,
        server: Server,
        template_name="main",
        title: str = "trame Slicer",
        theme: str = "dark",
        is_drawer_visible: bool = False,
    ):
        super().__init__(server, template_name=template_name)
        self.typed_state = TypedState(self.state, ViewerLayoutState)

        self.root.theme = theme
        self.title.set_text(title)

        with self:
            self.drawer = VNavigationDrawer(
                disable_resize_watcher=True,
                disable_route_watcher=True,
                permanent=True,
                location="left",
                v_model=(self.typed_state.name.is_drawer_visible, is_drawer_visible),
                width=350,
            )
            self.toolbar = VNavigationDrawer(
                classes="align-center py-3",
                disable_resize_watcher=True,
                disable_route_watcher=True,
                permanent=True,
                width=40,
                location="left",
            )
