from __future__ import annotations

from collections.abc import Generator

from numpy.typing import NDArray
from slicer import (
    vtkMRMLSegmentationNode,
    vtkMRMLVolumeNode,
    vtkOrientedImageData,
    vtkSegment,
    vtkSegmentation,
    vtkSegmentationConverter,
    vtkSlicerSegmentEditorLogic,
)
from undo_stack import Signal, UndoStack
from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkCommonDataModel import vtkImageData

from trame_slicer.utils import vtk_image_to_np

from .segment_properties import SegmentProperties
from .segmentation_display import SegmentationDisplay
from .segmentation_undo_command import (
    SegmentationAddUndoCommand,
    SegmentationRemoveUndoCommand,
    SegmentPropertyChangeUndoCommand,
)


class Segmentation:
    """
    Wrapper around vtkMRMLSegmentationNode for segmentation access.
    """

    segmentation_modified = Signal()

    def __init__(
        self,
        segmentation_node: vtkMRMLSegmentationNode,
        volume_node,
        *,
        editor_logic: vtkSlicerSegmentEditorLogic = None,
        undo_stack: UndoStack = None,
    ):
        self._editor_logic = editor_logic
        self._segmentation_node = segmentation_node
        self._volume_node = volume_node
        self._undo_stack = undo_stack
        self._node_obs = self._segmentation_node.AddObserver(
            vtkCommand.ModifiedEvent, lambda *_: self.segmentation_modified()
        )
        self.set_active()

    @property
    def editor_logic(self) -> vtkSlicerSegmentEditorLogic | None:
        return self._editor_logic

    def set_active(self):
        if not self.editor_logic:
            return
        self.editor_logic.SetSegmentationNode(self._segmentation_node)
        self.editor_logic.SetSourceVolumeNode(self._volume_node)
        self.editor_logic.UpdateReferenceGeometryImage()

    def set_undo_stack(self, undo_stack):
        if self._undo_stack == undo_stack:
            return

        if self._undo_stack:
            self._undo_stack.index_changed.disconnect(self._on_undo_changed)

        self._undo_stack = undo_stack
        if self._undo_stack:
            self._undo_stack.index_changed.connect(self._on_undo_changed)

    def set_segment_editor_logic(self, logic: vtkSlicerSegmentEditorLogic):
        self._editor_logic = logic

    @property
    def undo_stack(self) -> UndoStack | None:
        return self._undo_stack

    @property
    def segmentation(self) -> vtkSegmentation | None:
        return self._segmentation_node.GetSegmentation() if self._segmentation_node else None

    @property
    def segmentation_node(self) -> vtkMRMLSegmentationNode | None:
        return self._segmentation_node

    @property
    def volume_node(self) -> vtkMRMLVolumeNode | None:
        return self._volume_node

    @volume_node.setter
    def volume_node(self, volume_node):
        self._volume_node = volume_node

    @segmentation_node.setter
    def segmentation_node(self, segmentation_node):
        if self._segmentation_node == segmentation_node:
            return

        self._segmentation_node = segmentation_node
        self.segmentation_modified()

    def get_segment_ids(self) -> list[str]:
        if not self.segmentation:
            return []

        return list(self.segmentation.GetSegmentIDs())

    def get_segment_names(self) -> list[str]:
        if not self.segmentation:
            return []

        return [self.segmentation.GetNthSegment(i_segment).GetName() for i_segment in range(self.n_segments)]

    def get_segment_colors(self) -> list[list[float]]:
        if not self.segmentation:
            return []

        return [self.segmentation.GetNthSegment(i_segment).GetColor() for i_segment in range(self.n_segments)]

    @property
    def n_segments(self) -> int:
        return len(self.get_segment_ids())

    def get_nth_segment(self, i_segment: int) -> vtkSegment | None:
        if not self.segmentation or i_segment >= self.n_segments:
            return None
        return self.segmentation.GetNthSegment(i_segment)

    def get_nth_segment_id(self, i_segment: int) -> str:
        segment_ids = self.get_segment_ids()
        if i_segment < len(segment_ids):
            return segment_ids[i_segment]
        return ""

    def get_segment(self, segment_id: str) -> vtkSegment | None:
        if not self.segmentation or segment_id not in self.get_segment_ids():
            return None
        return self.segmentation.GetSegment(segment_id)

    def add_empty_segment(
        self,
        *,
        segment_id="",
        segment_name="",
        segment_color: list[float] | None = None,
        segment_value: int | None = None,
    ) -> str:
        if not self.segmentation:
            return ""

        cmd = SegmentationAddUndoCommand(
            self,
            segment_id,
            segment_name,
            segment_color,
            segment_value,
        )

        self.push_undo(cmd)
        self.segmentation_modified()
        return cmd.segment_id

    def remove_segment(self, segment_id) -> None:
        if not self.segmentation or segment_id not in self.get_segment_ids():
            return

        self.push_undo(SegmentationRemoveUndoCommand(self, segment_id))
        self.segmentation_modified()

    def get_segment_labelmap(self, segment_id, *, as_numpy_array=False) -> NDArray | vtkImageData:
        if not self.editor_logic or not self.editor_logic.GetSegmentEditorNode():
            return None

        node = self.editor_logic.GetSegmentEditorNode()
        prev = node.GetSelectedSegmentID()
        node.SetSelectedSegmentID(segment_id)

        self.editor_logic.UpdateSelectedSegmentLabelmap()
        labelmap = self.editor_logic.GetSelectedSegmentLabelmap()
        node.SetSelectedSegmentID(prev)

        return labelmap if not as_numpy_array else vtk_image_to_np(labelmap)

    @property
    def _surface_repr_name(self) -> str:
        return vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName()

    def _has_surface_repr(self) -> bool:
        if not self.editor_logic:
            return False
        return self.editor_logic.ContainsClosedSurfaceRepresentation()

    def set_surface_representation_enabled(self, is_enabled: bool) -> None:
        if not self.editor_logic:
            return
        self.editor_logic.ToggleSegmentationSurfaceRepresentation(is_enabled)

    def is_surface_representation_enabled(self) -> bool:
        return self._has_surface_repr()

    def enable_surface_representation(self) -> None:
        self.set_surface_representation_enabled(True)

    def disable_surface_representation(self) -> None:
        self.set_surface_representation_enabled(False)

    def get_visible_segment_ids(self) -> list[str]:
        if not self._segmentation_node:
            return []

        display_node = self._segmentation_node.GetDisplayNode()
        if not display_node:
            return []

        return [segment_id for segment_id in self.get_segment_ids() if display_node.GetSegmentVisibility(segment_id)]

    def get_segment_value(self, segment_id) -> int:
        segment = self.get_segment(segment_id)
        return segment.GetLabelValue() if segment else 0

    def set_segment_value(self, segment_id, segment_value: int | None):
        if segment_value is None:
            return

        segment_properties = self.get_segment_properties(segment_id)
        if segment_properties and segment_value:
            segment_properties.label_value = segment_value
            self.set_segment_properties(segment_id, segment_properties)

    @property
    def first_segment_id(self) -> str:
        return self.get_segment_ids()[0] if self.n_segments > 0 else ""

    def create_modifier_labelmap(self) -> vtkOrientedImageData | None:
        if not self._editor_logic:
            return None

        self._editor_logic.ResetModifierLabelmapToDefault()
        return self._editor_logic.GetModifierLabelmap()

    def trigger_modified(self):
        self.segmentation.Modified()
        self.segmentation_node.Modified()

    def get_segment_properties(self, segment_id) -> SegmentProperties | None:
        segment = self.get_segment(segment_id)
        return SegmentProperties.from_segment(segment) if segment is not None else None

    def set_segment_properties(self, segment_id, segment_properties: SegmentProperties):
        self.push_undo(SegmentPropertyChangeUndoCommand(self, segment_id, segment_properties))
        self.segmentation_modified()

    def push_undo(self, cmd):
        if self._undo_stack:
            self._undo_stack.push(cmd)

    def _on_undo_changed(self, *_):
        self.trigger_modified()

    def set_segment_labelmap(self, segment_id, label_map: vtkImageData | NDArray):
        if segment_id not in self.get_segment_ids():
            return

        if isinstance(label_map, vtkImageData):
            self.get_segment_labelmap(segment_id).DeepCopy(label_map)
        else:
            self.get_segment_labelmap(segment_id, as_numpy_array=True)[:] = label_map
        self.segmentation_modified()

    def get_display(self) -> SegmentationDisplay | None:
        return SegmentationDisplay(self._segmentation_node.GetDisplayNode()) if self._segmentation_node else None

    def group_undo_commands(self, text: str = "") -> Generator:
        return self.undo_stack.group_undo_commands(text)
