from __future__ import annotations

from slicer import vtkMRMLDisplayableNode, vtkMRMLVolumeNode

from .view_manager import ViewManager
from .volume_rendering import VolumeRendering


class DisplayManager:
    """
    Helper class to display volume nodes in given view group
    """

    def __init__(self, view_manager: ViewManager, volume_rendering: VolumeRendering):
        self._view_manager = view_manager
        self._vr = volume_rendering

    def show_volume(
        self,
        volume_node: vtkMRMLVolumeNode,
        view_group: int | None = None,
        vr_preset: str = "",
        do_reset_views: bool = False,
    ) -> None:
        if not volume_node:
            return

        self.show_volume_in_slice_background(volume_node, view_group)
        self.show_volume_in_slice_foreground(None, view_group)

        vr_display = (
            self._vr.create_display_node(volume_node, vr_preset)
            if not self._vr.has_vr_display_node(volume_node)
            else self._vr.get_vr_display_node(volume_node)
        )

        if vr_preset:
            self._vr.apply_preset(vr_display, vr_preset)

        vr_display.SetVisibility(True)
        self.set_node_visible_in_group(volume_node, view_group)

        if do_reset_views:
            self.reset_views(view_group)

    def reset_views(self, view_group: int | None = None):
        for view in self._view_manager.get_views(view_group):
            view.reset_view()

    def show_volume_in_slice_background(
        self,
        volume_node: vtkMRMLVolumeNode | None,
        view_group: int | None = None,
    ):
        for view in self._view_manager.get_slice_views(view_group):
            view.set_background_volume_id(volume_node.GetID() if volume_node else None)

    def show_volume_in_slice_foreground(
        self,
        volume_node: vtkMRMLVolumeNode | None,
        view_group: int | None = None,
    ):
        for view in self._view_manager.get_slice_views(view_group):
            view.set_foreground_volume_id(volume_node.GetID() if volume_node else None)

    def set_node_visible_in_group(
        self,
        node: vtkMRMLDisplayableNode,
        view_group: int | None = None,
    ):
        view_node_ids = [view.get_view_node_id() for view in self._view_manager.get_views(view_group)]

        for i_display in range(node.GetNumberOfDisplayNodes()):
            display = node.GetNthDisplayNode(i_display)
            if not display or display.GetDisplayableNode() != node:
                continue

            display.SetViewNodeIDs(view_node_ids)
