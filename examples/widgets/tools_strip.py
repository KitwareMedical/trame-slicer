from __future__ import annotations

from trame_client.widgets.html import Div
from trame_server import Server

from trame_slicer.core import LayoutManager, SlicerApp

from .layout_button import LayoutButton
from .load_client_volume_files_button import LoadClientVolumeFilesButton
from .markups_button import MarkupsButton
from .segmentation_button import SegmentationButton
from .volume_property_button import VolumePropertyButton


class ToolsStrip(Div):
    def __init__(
        self,
        *,
        server: Server,
        slicer_app: SlicerApp,
        layout_manager: LayoutManager,
        **kwargs,
    ):
        super().__init__(classes="bg-grey-darken-4 d-flex flex-column align-center", **kwargs)

        with self:
            LoadClientVolumeFilesButton(server=server, slicer_app=slicer_app)
            VolumePropertyButton(server=server, slicer_app=slicer_app)
            LayoutButton(
                server=server,
                slicer_app=slicer_app,
                layout_manager=layout_manager,
            )
            MarkupsButton(server=server, slicer_app=slicer_app)
            SegmentationButton(server=server, slicer_app=slicer_app)
