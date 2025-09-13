from typing import TypeVar

from slicer import vtkMRMLNode, vtkMRMLScene

T = TypeVar("T")


def ensure_node_in_scene(node: T | None, scene: vtkMRMLScene) -> T | None:
    """
    Ensure that the input node is properly registered in the scene.
    """
    if not isinstance(node, vtkMRMLNode) or not scene:
        return None

    if node.GetID() is None or scene.GetNodeByID(node.GetID()) is None:
        scene.AddNode(node)
    return node
