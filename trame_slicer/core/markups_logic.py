from __future__ import annotations

from slicer import (
    vtkMRMLApplicationLogic,
    vtkMRMLInteractionNode,
    vtkMRMLMarkupsNode,
    vtkMRMLScene,
    vtkSlicerMarkupsLogic,
)

from trame_slicer.utils import SlicerWrapper


class MarkupsLogic(SlicerWrapper):
    """
    Thin wrapper around vtkSlicerMarkupsLogic
    """

    def __init__(
        self,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
    ):
        super().__init__(slicer_obj=vtkSlicerMarkupsLogic())

        self._scene = scene
        self._logic.SetMRMLApplicationLogic(app_logic)
        self._logic.SetMRMLScene(scene)
        app_logic.SetModuleLogic("Markups", self._logic)

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
