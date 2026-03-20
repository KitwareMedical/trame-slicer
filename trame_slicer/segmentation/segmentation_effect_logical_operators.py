import numpy as np
from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLNode,
)

from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect


class SegmentationEffectLogicalOperators(SegmentationEffect):
    def __init__(self) -> None:
        super().__init__()

    def _create_pipeline(self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode) -> None:
        # Logical operators effect does not require a pipeline
        return None

    def add(self, segment_id: str):
        self.set_mode(ModificationMode.Add)
        self.modifier.apply_labelmap(self.modifier.segmentation.get_segment_labelmap(segment_id))

    def subtract(self, segment_id: str):
        active_segment_id = self.modifier.active_segment_id
        active_segment_labelmap = self.modifier.get_segment_labelmap(active_segment_id, as_numpy_array=True)
        other_segment_labelmap = self.modifier.get_segment_labelmap(segment_id, as_numpy_array=True)
        location = np.where(np.logical_and(active_segment_labelmap, other_segment_labelmap))
        active_segment_labelmap[location] = 0
        self.modifier.set_segment_labelmap(active_segment_id, active_segment_labelmap)

    def copy(self, segment_id: str):
        self.modifier.set_segment_labelmap(
            self.modifier.active_segment_id, self.modifier.get_segment_labelmap(segment_id)
        )

    def intersect(self, segment_id: str):
        active_segment_labelmap = self.modifier.get_segment_labelmap(
            self.modifier.active_segment_id, as_numpy_array=True
        )
        other_segment_labelmap = self.modifier.get_segment_labelmap(segment_id, as_numpy_array=True)
        active_segment_labelmap[np.where(np.logical_or(other_segment_labelmap == 0, active_segment_labelmap == 0))] = 0
        self.modifier.set_segment_labelmap(self.modifier.active_segment_id, active_segment_labelmap)

    def invert(self):
        active_segment_labelmap = self.modifier.get_segment_labelmap(
            self.modifier.active_segment_id, as_numpy_array=True
        )
        non_zero_coordinates = np.where(active_segment_labelmap)
        zero_coordinates = np.where(active_segment_labelmap == 0)
        new_segment_labelmap = active_segment_labelmap.copy()
        new_segment_labelmap[non_zero_coordinates] = 0
        new_segment_labelmap[zero_coordinates] = 1
        self.modifier.set_segment_labelmap(self.modifier.active_segment_id, new_segment_labelmap)

    def clear(self):
        active_segment_labelmap = self.modifier.get_segment_labelmap(
            self.modifier.active_segment_id, as_numpy_array=True
        )
        active_segment_labelmap = np.zeros_like(active_segment_labelmap, dtype=active_segment_labelmap.dtype)
        self.modifier.set_segment_labelmap(self.modifier.active_segment_id, active_segment_labelmap)

    def fill(self):
        active_segment_labelmap = self.modifier.get_segment_labelmap(
            self.modifier.active_segment_id, as_numpy_array=True
        )
        active_segment_labelmap = np.ones_like(active_segment_labelmap, dtype=active_segment_labelmap.dtype)
        self.modifier.set_segment_labelmap(self.modifier.active_segment_id, active_segment_labelmap)
