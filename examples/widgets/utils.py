from __future__ import annotations

from slicer import vtkMRMLVolumeNode
from trame_server import Server

from trame_slicer.core import SlicerApp


class IdName:
    def __set_name__(self, owner, name):
        self.name = name
        self.prefix = f"{owner.__qualname__}_"

    def __get__(self, obj, obj_type=None):
        return self.prefix + self.name


class StateId:
    current_volume_node_id = IdName()
    current_layout_name = IdName()
    file_loading_busy = IdName()
    vr_slider_value = IdName()
    vr_slider_min = IdName()
    vr_slider_max = IdName()
    vr_presets = IdName()
    vr_preset_value = IdName()


def get_current_volume_node(server: Server, slicer_app: SlicerApp) -> vtkMRMLVolumeNode | None:
    node_id = server.state[StateId.current_volume_node_id]
    if not node_id:
        return None
    return slicer_app.scene.GetNodeByID(node_id)
