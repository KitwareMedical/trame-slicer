from __future__ import annotations

from collections import deque

from slicer import vtkSegmentation


class SegmentationStateStack:
    """
    Simple segmentation stack.
    Deep copies input segmentation when saving state.
    Not optimized by any means.
    """

    def __init__(self, segmentation: vtkSegmentation, max_size: int):
        self._segmentation = segmentation
        self._max_size = max_size
        self._segmentation_states: deque[vtkSegmentation] | None = None
        self._index = -1
        self.clear()

    def _create_segmentation_clone(self) -> vtkSegmentation:
        s_clone = vtkSegmentation()
        s_clone.DeepCopy(self._segmentation)
        return s_clone

    def save_state(self) -> None:
        self.remove_next_states()
        self._segmentation_states.append(self._create_segmentation_clone())
        self._index = len(self._segmentation_states) - 1

    def clear(self) -> None:
        self._segmentation_states = deque(maxlen=self._max_size)
        self._index = -1

    def has_next(self):
        return self._index < len(self._segmentation_states) - 1

    def has_previous(self):
        return self._index > 0

    def restore_next(self):
        """
        Restore next saved state if stack has following states.
        """

        if not self.has_next():
            return

        self._apply_segmentation_state(self._segmentation_states[self._index + 1])
        self._index += 1

    def restore_previous(self):
        """
        Restore previous state if stack has previous states.
        """
        if not self.has_previous():
            return

        self._apply_segmentation_state(self._segmentation_states[self._index - 1])
        self._index -= 1

    def remove_next_states(self) -> None:
        """
        Pops all next states.
        """
        while self.has_next():
            self._segmentation_states.pop()

    def set_max_size(self, max_size: int) -> None:
        if max_size == self._max_size:
            return
        self._max_size = max_size
        self.clear()

    def get_max_size(self) -> int:
        return self._max_size

    def _apply_segmentation_state(self, state: vtkSegmentation) -> None:
        self._segmentation.DeepCopy(state)

    def __len__(self) -> int:
        return len(self._segmentation_states)
