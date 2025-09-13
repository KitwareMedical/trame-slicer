from __future__ import annotations

from contextlib import contextmanager

from slicer import vtkMRMLNode


@contextmanager
def mrml_node_modify_blocker(node):
    if not isinstance(node, vtkMRMLNode):
        yield
        return

    was_modifying = node.StartModify()
    try:
        yield
    finally:
        node.EndModify(was_modifying)
