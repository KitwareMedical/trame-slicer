from __future__ import annotations

from slicer import vtkMRMLScene, vtkMRMLScriptedModuleNode
from trame_client.ui.core import AbstractLayout
from trame_client.widgets.core import VirtualNode
from trame_server import Server
from undo_stack import Signal

from trame_slicer.views import (
    Layout,
    LayoutDirection,
    LayoutGrid,
    ViewLayoutDefinition,
    pretty_xml,
    slicer_layout_to_vue,
    vue_layout_to_slicer,
)

from .view_manager import ViewManager


class LayoutManager:
    """
    Class responsible for instantiating views depending on the layout node.
        - Creates a singleton layout node at initialization.
        - Observes layout node changes to notify observers of layout id changes.
        - Can register layouts with their associated descriptions
        - Notifies view manager of requested view on layout change
    """

    registered_layouts_changed = Signal()
    current_layout_changed = Signal()

    def __init__(
        self,
        scene: vtkMRMLScene,
        view_manager: ViewManager,
        server: Server,
        *,
        virtual_node: VirtualNode | None = None,
        is_virtual_node_initialized: bool = False,
    ):
        self._layouts: dict[str, Layout] = {}
        self._view_manager = view_manager
        self._virtual_node = virtual_node or VirtualNode(server)
        self._current_layout: str | None = None
        self._scene_node = scene.AddNewNodeByClass("vtkMRMLScriptedModuleNode", "layout_node")
        self._is_virtual_node_initialized = is_virtual_node_initialized

    def get_layout_ids(self) -> list[str]:
        return list(self._layouts.keys())

    def register_layout(self, layout_id: str, layout: Layout, lazy_initialization: bool = False) -> None:
        """
        Registers the given layout id to the associated layout.
        Will overwrite any pre existing layout with this ID.
        If lazy_initialization is False, the views will not be instantiated unless the passed layout id matches the
        current selected layout id.
        """
        with self.registered_layouts_changed.emit_once():
            self._layouts[layout_id] = layout
            if not lazy_initialization:
                self.create_layout_views_if_needed(layout_id)

            if self._current_layout == layout_id:
                self._refresh_layout()

    def set_layout(self, layout_id: str) -> None:
        if layout_id == self._current_layout:
            return

        with self.current_layout_changed.emit_once():
            self._current_layout = layout_id
            self._refresh_layout()

    def create_layout_views_if_needed(self, layout_id: str) -> None:
        self._create_views_if_needed(self.get_layout(layout_id, Layout.empty_layout()))

    def _refresh_layout(self):
        # Don't refresh layout when the current layout is None or when the virtual node is not yet bound to a layout.
        if not self._is_virtual_node_initialized or self._current_layout is None:
            return

        layout = self.get_layout(self._current_layout, Layout.empty_layout())
        self.create_layout_views_if_needed(self._current_layout)
        self._set_current_views_as_active(layout)
        with self._virtual_node.clear():
            LayoutGrid.create_root_grid_ui(layout)
        self._save_layout_to_scene(self._current_layout, layout)

    def _create_views_if_needed(self, layout: Layout) -> None:
        views = layout.get_views(is_recursive=True)
        for view in views:
            if not self._view_manager.is_view_created(view.singleton_tag):
                self._view_manager.create_view(view)

    def _set_current_views_as_active(self, layout: Layout) -> None:
        views = layout.get_views(is_recursive=True)
        view_ids = [view.singleton_tag for view in views]
        self._view_manager.set_current_view_ids(view_ids)

    def _save_layout_to_scene(self, layout_id: str, layout: Layout) -> None:
        self._scene_node.SetParameter("layout_id", layout_id)
        self._scene_node.SetParameter("layout_description", pretty_xml(vue_layout_to_slicer(layout)))

    def set_layout_from_node(self, node: vtkMRMLScriptedModuleNode) -> None:
        if not node:
            _error_msg = "Cannot set layout from None scene node."
            raise RuntimeError(_error_msg)

        layout_id = node.GetParameter("layout_id")
        layout_description = node.GetParameter("layout_description")
        if None in [layout_id, layout_description]:
            _error_msg = f"Invalid layout information {layout_id}, {layout_description}"
            raise RuntimeError(_error_msg)

        self.register_layout(layout_id, slicer_layout_to_vue(layout_description), lazy_initialization=True)
        self.set_layout(layout_id)

    def has_layout(self, layout_id: str) -> bool:
        return layout_id in self._layouts

    def get_layout(self, layout_id: str, default_layout: Layout | None = None) -> Layout:
        if not self.has_layout(layout_id) and default_layout is None:
            _error_msg = f"Layout not present in manager : {layout_id}"
            raise RuntimeError(_error_msg)

        return self._layouts.get(layout_id, default_layout)

    def register_layout_dict(self, layout_dict: dict[str, Layout], lazy_initialization: bool = False) -> None:
        """
        :param layout_dict: Layout dictionary to register to the layout manager
        :param lazy_initialization: If True, the layout views will not be created until explicitly requested by
            set_layout or create_layout_views_if_needed
        """
        for layout_id, layout in layout_dict.items():
            self.register_layout(layout_id, layout, lazy_initialization)

    @classmethod
    def default_grid_configuration(cls) -> dict[str, Layout]:
        axial_view = ViewLayoutDefinition.axial_view()
        coronal_view = ViewLayoutDefinition.coronal_view()
        sagittal_view = ViewLayoutDefinition.sagittal_view()
        threed_view = ViewLayoutDefinition.threed_view()

        return {
            "Axial Only": Layout(LayoutDirection.Vertical, [axial_view]),
            "Axial Primary": Layout(
                LayoutDirection.Horizontal,
                [
                    axial_view,
                    Layout(
                        LayoutDirection.Vertical,
                        [threed_view, coronal_view, sagittal_view],
                    ),
                ],
            ),
            "3D Primary": Layout(
                LayoutDirection.Horizontal,
                [
                    threed_view,
                    Layout(
                        LayoutDirection.Vertical,
                        [axial_view, coronal_view, sagittal_view],
                    ),
                ],
            ),
            "Quad View": Layout(
                LayoutDirection.Horizontal,
                [
                    Layout(
                        LayoutDirection.Vertical,
                        [coronal_view, sagittal_view],
                    ),
                    Layout(
                        LayoutDirection.Vertical,
                        [threed_view, axial_view],
                    ),
                ],
            ),
            "3D Only": Layout(LayoutDirection.Vertical, [threed_view]),
        }

    def initialize_layout_grid(self, layout: AbstractLayout):
        """
        Initialize the LayoutGrid placeholder in the layout at the call position.
        """
        self._virtual_node(layout)
        self._is_virtual_node_initialized = True
        self._refresh_layout()
