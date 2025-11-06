from dataclasses import dataclass

from trame_client.widgets.core import VirtualNode
from trame_server import Server
from trame_server.utils.typed_state import TypedState
from trame_vuetify.ui.vuetify3 import SinglePageLayout
from trame_vuetify.widgets.vuetify3 import VContainer, VNavigationDrawer


@dataclass
class MedicalViewerLayoutState:
    is_drawer_visible: bool = False
    active_drawer_ui: str = ""


class MedicalViewerLayout(SinglePageLayout):
    def __init__(
        self,
        server: Server,
        template_name="main",
        title: str = "trame Slicer",
        theme: str = "dark",
        is_drawer_visible: bool = False,
    ):
        super().__init__(server, template_name=template_name)
        self.typed_state = TypedState(self.state, MedicalViewerLayoutState)
        self.typed_state.data.is_drawer_visible = is_drawer_visible

        self.root.theme = theme
        self.title.set_text(title)
        self.drawer = VirtualNode(server)
        self.icon.click = f"{self.typed_state.name.is_drawer_visible} = !{self.typed_state.name.is_drawer_visible}"

        with self:
            with (
                VNavigationDrawer(
                    disable_resize_watcher=True,
                    disable_route_watcher=True,
                    permanent=True,
                    location="left",
                    v_model=(self.typed_state.name.is_drawer_visible,),
                    width=300,
                ),
                VContainer(),
            ):
                self.drawer()

            with VNavigationDrawer(
                disable_resize_watcher=True,
                disable_route_watcher=True,
                permanent=True,
                rail=True,
                location="left",
            ):
                self.toolbar = VContainer(classes="d-flex flex-column align-center justify-center pa-0 ma-0 fill-width")
