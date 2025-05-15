from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from enum import Flag, auto

import numpy as np
from numpy.typing import NDArray
from slicer import (
    vtkMRMLSegmentationNode,
    vtkMRMLVolumeNode,
    vtkSegment,
    vtkSegmentation,
    vtkSegmentationConverter,
    vtkSlicerSegmentationGeometryLogic,
)
from undo_stack import Signal, UndoCommand, UndoStack
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_CHAR, vtkCommand
from vtkmodules.vtkCommonDataModel import vtkImageData

from trame_slicer.utils import vtk_image_to_np

from .segment_properties import SegmentProperties


class SegmentationOpacityEnum(Flag):
    FILL = auto()
    OUTLINE = auto()
    BOTH = FILL | OUTLINE

    @classmethod
    def toggle_order(cls):
        return [cls.BOTH, cls.OUTLINE, cls.FILL]

    def next(self):
        values = self.toggle_order()
        return values[(values.index(self) + 1) % len(values)]


class SegmentationRemoveUndoCommand(UndoCommand):
    def __init__(self, segmentation: Segmentation, segment_id):
        super().__init__()
        self._segmentation = segmentation
        self.segment_id = segment_id
        self._segment_properties = SegmentProperties.from_segment(segmentation.get_segment(segment_id))
        self._label_map = deepcopy(self._segmentation.get_segment_labelmap(segment_id, as_numpy_array=True))
        self.redo()

    def undo(self) -> None:
        self._segmentation.segmentation.AddEmptySegment(self.segment_id)
        self._segment_properties.to_segment(self._segmentation.get_segment(self.segment_id))
        self._segmentation.set_segment_labelmap(self.segment_id, self._label_map)

    def redo(self) -> None:
        self._segmentation.segmentation.RemoveSegment(self.segment_id)


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

    def redo(self) -> None:
        self._segmentation.segmentation.AddEmptySegment(self.segment_id)
        self._segment_properties.to_segment(self._segmentation.get_segment(self.segment_id))

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

    def redo(self) -> None:
        self._properties.to_segment(self._segment)

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
    def __init__(
        self,
        segmentation: Segmentation,
        prev_label_map_dict: dict[str, vtkImageData],
        next_label_map_dict: dict[str, vtkImageData],
    ):
        super().__init__()
        self._segmentation = segmentation
        self._prev_labelmap = prev_label_map_dict
        self._next_labelmap = next_label_map_dict

    def undo(self) -> None:
        self._apply_label_map_dict(self._prev_labelmap)

    def redo(self) -> None:
        self._apply_label_map_dict(self._next_labelmap)

    def _apply_label_map_dict(self, label_map_dict):
        with self._segmentation.segmentation_modified.emit_blocked():
            for segment_id, label_map in label_map_dict.items():
                self._segmentation.set_segment_labelmap(segment_id, label_map)
        self._segmentation.trigger_modified()

    @classmethod
    @contextmanager
    def push_state_change(cls, segmentation: Segmentation):
        if not segmentation.undo_stack or not segmentation.first_segment_id:
            yield
            return

        prev_label_map = {
            s: deepcopy(segmentation.get_segment_labelmap(s, as_numpy_array=True))
            for s in segmentation.get_segment_ids()
        }
        yield
        next_label_map = {
            s: deepcopy(segmentation.get_segment_labelmap(s, as_numpy_array=True))
            for s in segmentation.get_segment_ids()
        }
        segmentation.undo_stack.push(cls(segmentation, prev_label_map, next_label_map))

    @classmethod
    def copy_label_map(cls, segmentation: Segmentation) -> dict[str, vtkImageData]:
        """
        Copy labelmap values as dict of segment_id to labelmap.
        If all segment ids map to the same labelmap, only keep one labelmap.
        """
        labelmap_dict = defaultdict(list)
        for segment_id in segmentation.get_segment_ids():
            labelmap_dict[segmentation.get_segment_labelmap(segment_id)].append(segment_id)

        out_dict = {}
        for image, segment_ids in labelmap_dict.items():
            new_image = vtkImageData()
            new_image.DeepCopy(image)
            for segment_id in segment_ids:
                out_dict[segment_id] = new_image

        return out_dict


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
        undo_stack: UndoStack = None,
    ):
        self._segmentation_node = segmentation_node
        self._volume_node = volume_node
        self._is_surface_repr_enabled = self._has_surface_repr()
        self._undo_stack = undo_stack
        self.segmentation_modified.connect(self.update_surface_representation)
        self._node_obs = self._segmentation_node.AddObserver(
            vtkCommand.ModifiedEvent, lambda *_: self.segmentation_modified()
        )

    def __del__(self):
        self.segmentation_node.RemoveObserver(self._node_obs)

    def set_undo_stack(self, undo_stack):
        if self._undo_stack == undo_stack:
            return

        if self._undo_stack:
            self._undo_stack.index_changed.disconnect(self._on_undo_changed)

        self._undo_stack = undo_stack
        if self._undo_stack:
            self._undo_stack.index_changed.connect(self._on_undo_changed)

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
        self._is_surface_repr_enabled = self._has_surface_repr()
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

    def get_segment_labelmap(self, segment_id, *, as_numpy_array=False, do_sanitize=True) -> NDArray | vtkImageData:
        if do_sanitize and self._needs_sanitize():
            self.sanitize_segmentation(self.segmentation_node, self.volume_node)

        return self._get_segment_labelmap(segment_id, as_numpy_array=as_numpy_array)

    def _get_segment_labelmap(self, segment_id, *, as_numpy_array=False) -> NDArray | vtkImageData:
        def empty():
            return vtkImageData() if not as_numpy_array else np.array([])

        if not segment_id or not self.segmentation:
            return empty()

        segment = self.segmentation.GetSegment(segment_id)
        if not segment:
            return empty()

        labelmap = segment.GetRepresentation(vtkSegmentationConverter.GetBinaryLabelmapRepresentationName())
        return labelmap if not as_numpy_array else vtk_image_to_np(labelmap)

    @property
    def _surface_repr_name(self) -> str:
        return vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName()

    def _has_surface_repr(self) -> bool:
        if not self.segmentation:
            return False
        return self.segmentation.ContainsRepresentation(self._surface_repr_name)

    def set_surface_representation_enabled(self, is_enabled: bool) -> None:
        self._is_surface_repr_enabled = is_enabled
        self.segmentation_modified()

    def is_surface_representation_enabled(self) -> bool:
        return self._is_surface_repr_enabled

    def enable_surface_representation(self) -> None:
        self.set_surface_representation_enabled(True)

    def disable_surface_representation(self) -> None:
        self.set_surface_representation_enabled(False)

    def update_surface_representation(self) -> None:
        if not self.n_segments:
            return

        if self._is_surface_repr_enabled:
            self.segmentation.CreateRepresentation(self._surface_repr_name, True)
        else:
            self.segmentation.RemoveRepresentation(self._surface_repr_name)

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

    def create_modifier_labelmap(self) -> vtkImageData | None:
        vtk_labelmap = self.get_segment_labelmap(self.first_segment_id)
        if not vtk_labelmap:
            return None

        labelmap = vtkImageData()
        labelmap.SetExtent(list(vtk_labelmap.GetExtent()))
        labelmap.AllocateScalars(VTK_UNSIGNED_CHAR, 1)  # booleans
        labelmap.GetPointData().GetScalars().Fill(0)
        return labelmap

    @staticmethod
    def sanitize_segmentation(segmentation_node, volume_node):
        logic = vtkSlicerSegmentationGeometryLogic()
        logic.SetInputSegmentationNode(segmentation_node)
        logic.SetSourceGeometryNode(volume_node)
        logic.CalculateOutputGeometry()
        logic.SetReferenceImageGeometryInSegmentationNode()
        logic.ResampleLabelmapsInSegmentationNode()
        segmentation_node.GetSegmentation().SetSourceRepresentationName(
            vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName()
        )

    def _sanitize_segmentation_if_needed(self):
        if not self._needs_sanitize():
            return

        self.sanitize_active_segmentation()

    def sanitize_active_segmentation(self):
        self.sanitize_segmentation(self.segmentation_node, self.volume_node)

    def _needs_sanitize(self):
        if not self.first_segment_id or not self._volume_node:
            return False

        volume_extents = self.volume_node.GetImageData().GetExtent()
        labelmap_extents = self._get_segment_labelmap(self.first_segment_id).GetExtent()
        return not all(v_extent == l_extent for v_extent, l_extent in zip(volume_extents, labelmap_extents))

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

    def set_segment_visibility(self, segment_id, visibility: bool) -> None:
        if segment_id not in self.get_segment_ids():
            return

        display_node = self._segmentation_node.GetDisplayNode()
        display_node.SetSegmentVisibility(segment_id, visibility)

    def get_segment_visibility(self, segment_id) -> bool | None:
        if segment_id not in self.get_segment_ids():
            return None

        display_node = self._segmentation_node.GetDisplayNode()
        return display_node.GetSegmentVisibility(segment_id)

    def set_opacity_mode(self, opacity_mode: SegmentationOpacityEnum) -> None:
        if not self._segmentation_node:
            return
        display_node = self._segmentation_node.GetDisplayNode()
        display_node.SetVisibility2DFill(SegmentationOpacityEnum.FILL in opacity_mode)
        display_node.SetVisibility2DOutline(SegmentationOpacityEnum.OUTLINE in opacity_mode)

    def get_opacity_mode(self) -> SegmentationOpacityEnum | None:
        if not self._segmentation_node:
            return None
        display_node = self._segmentation_node.GetDisplayNode()
        fill_visibility = display_node.GetVisibility2DFill()
        outline_visibility = display_node.GetVisibility2DOutline()
        if outline_visibility and not fill_visibility:
            return SegmentationOpacityEnum.OUTLINE
        if fill_visibility and not outline_visibility:
            return SegmentationOpacityEnum.FILL
        return SegmentationOpacityEnum.FILL | SegmentationOpacityEnum.OUTLINE

    def get_2d_opacity(self) -> float | None:
        if not self._segmentation_node:
            return None
        display_node = self._segmentation_node.GetDisplayNode()
        return display_node.GetOpacity2DFill()

    def set_2d_opacity(self, opacity: float) -> None:
        if not self._segmentation_node:
            return
        display_node = self._segmentation_node.GetDisplayNode()
        display_node.SetOpacity2DFill(opacity)
        display_node.SetOpacity2DOutline(opacity)

    def get_3d_opacity(self) -> float | None:
        if not self._segmentation_node:
            return None
        display_node = self._segmentation_node.GetDisplayNode()
        return display_node.GetOpacity3D()

    def set_3d_opacity(self, opacity: float) -> None:
        if not self._segmentation_node:
            return
        display_node = self._segmentation_node.GetDisplayNode()
        display_node.SetOpacity3D(opacity)
