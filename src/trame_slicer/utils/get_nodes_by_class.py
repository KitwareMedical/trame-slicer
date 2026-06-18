from slicer import vtkMRMLNode, vtkMRMLScene


def get_nodes_by_class(class_name: str, scene: vtkMRMLScene) -> list[vtkMRMLNode]:
    """
    Adapted from slicer.util.getNodesByClass to inject the input scene.
    Returns the nodes associated with the input class_name without leaking the node collection.
    """
    nodes = scene.GetNodesByClass(class_name)
    nodes.UnRegister(scene)
    node_list = []
    nodes.InitTraversal()
    node = nodes.GetNextItemAsObject()
    while node:
        node_list.append(node)
        node = nodes.GetNextItemAsObject()
    return node_list
