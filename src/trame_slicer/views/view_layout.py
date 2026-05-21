from __future__ import annotations

from trame.widgets import html
from trame_client.ui.core import AbstractLayout
from trame_server import Server


class ViewLayout(AbstractLayout):
    def __init__(self, server: Server, template_name: str):
        """
        :param server: Server to bound the layout to
        :param template_name: Name of the template (default: main)
        """
        super().__init__(
            server,
            html.Div(trame_server=server, style="height:100%; width:100%;"),
            template_name=template_name,
        )
