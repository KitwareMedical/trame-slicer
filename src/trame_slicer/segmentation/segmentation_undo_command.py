from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from undo_stack import UndoCommand

from .segment_properties import SegmentProperties
from .segmentation_state_stack import SegmentationStateStack

if TYPE_CHECKING:
    from .segmentation import Segmentation


class SegmentationRemoveUndoCommand(UndoCommand):
    def __init__(self, segmentation: Segmentation, segment_id):
        super().__init__()
        self.segment_id = segment_id
        self._segmentation = segmentation
        self._segmentation_state_stack = SegmentationStateStack(segmentation.segmentation, max_size=2)
        self._segmentation_state_stack.save_state()
        self._segmentation.segmentation.RemoveSegment(self.segment_id)
        self._segmentation_state_stack.save_state()

    def undo(self) -> None:
        self._segmentation_state_stack.restore_previous()
        self._segmentation.trigger_modified()

    def redo(self) -> None:
        self._segmentation_state_stack.restore_next()
        self._segmentation.trigger_modified()


class SegmentationAddUndoCommand(UndoCommand):
    def __init__(
        self,
        segmentation: Segmentation,
        segment_id,
        segment_name,
        segment_color,
        segment_value,
    ):
        super().__init__()
        self._segmentation = segmentation

        self.segment_id = self._segmentation.segmentation.AddEmptySegment(segment_id, segment_name, segment_color)
        segment = self._segmentation.get_segment(self.segment_id)
        if segment_value is not None:
            segment.SetLabelValue(segment_value)
        self._segment_properties = SegmentProperties.from_segment(segment)

    def undo(self) -> None:
        self._segmentation.segmentation.RemoveSegment(self.segment_id)
        self._segmentation.trigger_modified()

    def redo(self) -> None:
        self._segmentation.segmentation.AddEmptySegment(self.segment_id)
        self._segment_properties.to_segment(self._segmentation.get_segment(self.segment_id))
        self._segmentation.trigger_modified()

    def merge_with(self, command: UndoCommand) -> bool:
        if not isinstance(command, SegmentationRemoveUndoCommand):
            return False

        if command.segment_id != self.segment_id:
            return False

        self._is_obsolete = True
        return True

    def do_try_merge(self, command: UndoCommand) -> bool:
        return isinstance(command, SegmentationRemoveUndoCommand)


class SegmentPropertyChangeUndoCommand(UndoCommand):
    """
    Undo / Redo command for segment property changes.
    Property changes can be compressed if they apply to the same segment.
    """

    def __init__(
        self,
        segmentation: Segmentation,
        segment_id: str,
        segment_properties: SegmentProperties,
    ):
        super().__init__()
        self._id = self.__class__.__name__
        self._segmentation = segmentation
        self._segment_id = segment_id
        self._prev_properties = SegmentProperties.from_segment(self._segment)
        self._properties = segment_properties
        self.redo()

    def is_obsolete(self) -> bool:
        return self._prev_properties is None

    def undo(self) -> None:
        if not self._prev_properties:
            return

        self._prev_properties.to_segment(self._segment)
        self._segmentation.trigger_modified()

    def redo(self) -> None:
        self._properties.to_segment(self._segment)
        self._segmentation.trigger_modified()

    @property
    def _segment(self):
        return self._segmentation.get_segment(self._segment_id)

    def merge_with(self, command: UndoCommand) -> bool:
        if not isinstance(command, SegmentPropertyChangeUndoCommand):
            return False

        if self._segment != command._segment:
            return False

        self._properties = command._properties
        return True


class SegmentationLabelMapUndoCommand(UndoCommand):
    def __init__(self, segmentation_stack: SegmentationStateStack, segmentation: Segmentation):
        super().__init__()
        self._segmentation_stack = segmentation_stack
        self._segmentation = segmentation

    def undo(self) -> None:
        self._segmentation_stack.restore_previous()
        self._segmentation.trigger_modified()

    def redo(self) -> None:
        self._segmentation_stack.restore_next()
        self._segmentation.trigger_modified()

    @classmethod
    @contextmanager
    def push_state_change(cls, segmentation: Segmentation):
        if not segmentation.undo_stack or not segmentation.segmentation or not segmentation.segmentation_node:
            yield
            return

        segmentation_state_stack = SegmentationStateStack(segmentation.segmentation, max_size=2)
        segmentation_state_stack.save_state()
        yield
        segmentation_state_stack.save_state()
        segmentation.undo_stack.push(cls(segmentation_state_stack, segmentation))
