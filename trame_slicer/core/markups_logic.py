from __future__ import annotations

from typing import TYPE_CHECKING

from slicer import (
    vtkMRMLInteractionNode,
    vtkMRMLMarkupsNode,
    vtkSlicerMarkupsLogic,
)

from trame_slicer.utils import SlicerWrapper

if TYPE_CHECKING:
    from .slicer_app import SlicerApp


class MarkupsLogic(SlicerWrapper):
    """
    Thin wrapper around vtkSlicerMarkupsLogic
    """

    def __init__(self, slicer_app: SlicerApp):
        super().__init__(slicer_obj=vtkSlicerMarkupsLogic())
        self._scene = slicer_app.scene
        slicer_app.register_module_logic(self._logic)

    @property
    def _logic(self) -> vtkSlicerMarkupsLogic:
        return self._slicer_obj

    @property
    def interaction_node(self) -> vtkMRMLInteractionNode | None:
        return self._scene.GetNodeByID("vtkMRMLInteractionNodeSingleton")

    def _raise_if_invalid_interaction_node(self):
        if not self.interaction_node:
            _error_msg = f"Invalid scene interaction node '{self.interaction_node}'"
            raise RuntimeError(_error_msg)

    def place_node(self, node: vtkMRMLMarkupsNode, persistent: bool = False):
        self._raise_if_invalid_interaction_node()
        self._logic.SetActiveList(node)
        self.interaction_node.SetPlaceModePersistence(persistent)
        self.interaction_node.SetCurrentInteractionMode(vtkMRMLInteractionNode.Place)

    def disable_place_mode(self):
        self._raise_if_invalid_interaction_node()
        self.interaction_node.SetCurrentInteractionMode(vtkMRMLInteractionNode.ViewTransform)
