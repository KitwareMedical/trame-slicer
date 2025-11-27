from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from numpy.typing import NDArray
from slicer import (
    vtkMRMLScene,
    vtkMRMLSegmentationNode,
    vtkMRMLSegmentEditorNode,
    vtkMRMLVolumeNode,
    vtkOrientedImageData,
    vtkSegment,
    vtkSegmentation,
    vtkSegmentationConverter,
    vtkSlicerSegmentEditorLogic,
)
from undo_stack import Signal, UndoStack
from vtkmodules.vtkCommonCore import vtkCommand, vtkStringArray
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonMath import vtkMatrix4x4

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
        volume_node: vtkMRMLVolumeNode,
        *,
        scene: vtkMRMLScene | None = None,
        undo_stack: UndoStack = None,
    ):
        assert segmentation_node, "Segmentation expects a valid segmentation node at creation"
        assert volume_node, "Segmentation expects a valid volume node at creation"

        self._scene = scene or volume_node.GetMRMLScene()
        self._editor_node = self._create_editor_node(scene=self._scene)
        self._editor_logic = self._create_editor_logic(scene=self._scene, editor_node=self._editor_node)
        self._segmentation_node = segmentation_node
        self._volume_node = volume_node
        self._undo_stack = undo_stack
        self._node_obs = self._segmentation_node.AddObserver(
            vtkCommand.ModifiedEvent, lambda *_: self.segmentation_modified()
        )
        self._update_editor_logic()

    @property
    def editor_logic(self) -> vtkSlicerSegmentEditorLogic:
        return self._editor_logic

    def _update_editor_logic(self) -> None:
        self._editor_logic.SetSegmentationNode(self._segmentation_node)
        self._editor_logic.SetSourceVolumeNode(self._volume_node)
        self._editor_logic.UpdateReferenceGeometryImage()

    def set_undo_stack(self, undo_stack: UndoStack | None) -> None:
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
    def segmentation(self) -> vtkSegmentation:
        return self._segmentation_node.GetSegmentation()

    @property
    def segmentation_node(self) -> vtkMRMLSegmentationNode:
        return self._segmentation_node

    @property
    def volume_node(self) -> vtkMRMLVolumeNode:
        return self._volume_node

    @volume_node.setter
    def volume_node(self, volume_node: vtkMRMLVolumeNode) -> None:
        assert volume_node, "Segmentation expects a valid volume_node instance"
        if self._volume_node == volume_node:
            return
        self._volume_node = volume_node
        self._update_editor_logic()

    @segmentation_node.setter
    def segmentation_node(self, segmentation_node: vtkMRMLSegmentationNode) -> None:
        assert segmentation_node, "Segmentation expects a valid segmentation_node instance"
        if self._segmentation_node == segmentation_node:
            return

        self._segmentation_node = segmentation_node
        self._update_editor_logic()
        self.segmentation_modified()

    def get_segment_ids(self) -> list[str]:
        return list(self.segmentation.GetSegmentIDs())

    def get_segment_names(self) -> list[str]:
        return [self.segmentation.GetNthSegment(i_segment).GetName() for i_segment in range(self.n_segments)]

    def get_segment_colors(self) -> list[list[float]]:
        return [self.segmentation.GetNthSegment(i_segment).GetColor() for i_segment in range(self.n_segments)]

    @property
    def n_segments(self) -> int:
        return len(self.get_segment_ids())

    def get_nth_segment(self, i_segment: int) -> vtkSegment | None:
        if i_segment >= self.n_segments:
            return None
        return self.segmentation.GetNthSegment(i_segment)

    def get_nth_segment_id(self, i_segment: int) -> str:
        segment_ids = self.get_segment_ids()
        if i_segment < len(segment_ids):
            return segment_ids[i_segment]
        return ""

    def get_segment(self, segment_id: str) -> vtkSegment | None:
        if segment_id not in self.get_segment_ids():
            return None
        return self.segmentation.GetSegment(segment_id)

    def add_empty_segment(
        self,
        *,
        segment_id: str = "",
        segment_name: str = "",
        segment_color: list[float] | None = None,
        segment_value: int | None = None,
    ) -> str:
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

    def remove_segment(self, segment_id: str) -> None:
        if segment_id not in self.get_segment_ids():
            return

        self.push_undo(SegmentationRemoveUndoCommand(self, segment_id))
        self.segmentation_modified()

    def get_segment_labelmap(self, segment_id: str, *, as_numpy_array: bool = False) -> NDArray | vtkImageData:
        if segment_id not in self.get_segment_ids():
            _error_msg = f"Segment id: {segment_id} doesn't exist in segment list: {self.get_segment_ids()}"
            raise ValueError(_error_msg)

        prev = self.editor_node.GetSelectedSegmentID()
        self.editor_node.SetSelectedSegmentID(segment_id)
        labelmap = self.get_selected_segment_label_map()
        self.editor_node.SetSelectedSegmentID(prev)

        return labelmap if not as_numpy_array else vtk_image_to_np(labelmap)

    @property
    def _surface_repr_name(self) -> str:
        return vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName()

    def _has_surface_repr(self) -> bool:
        return self.editor_logic.ContainsClosedSurfaceRepresentation()

    def set_surface_representation_enabled(self, is_enabled: bool) -> None:
        self.editor_logic.ToggleSegmentationSurfaceRepresentation(is_enabled)

    def is_surface_representation_enabled(self) -> bool:
        return self._has_surface_repr()

    def enable_surface_representation(self) -> None:
        self.set_surface_representation_enabled(True)

    def disable_surface_representation(self) -> None:
        self.set_surface_representation_enabled(False)

    def get_visible_segment_ids(self) -> list[str]:
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
        self._editor_logic.ResetModifierLabelmapToDefault()
        label_map = self._editor_logic.GetModifierLabelmap()
        self._set_label_map_transform_to_volume_transform(label_map)
        return label_map

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

    @contextmanager
    def group_undo_commands(self, text: str = "") -> Generator:
        if not self.undo_stack:
            yield
            return

        with self.undo_stack.group_undo_commands(text):
            yield

    def get_source_image_data(self) -> vtkOrientedImageData | None:
        self._editor_logic.UpdateAlignedSourceVolume()
        return self._editor_logic.GetAlignedSourceVolume()

    def get_merged_label_map(self, segment_ids: list[str] | None = None) -> vtkOrientedImageData | None:
        label_map = vtkOrientedImageData()
        self.segmentation_node.GenerateMergedLabelmapForAllSegments(
            label_map,
            vtkSegmentation.EXTENT_REFERENCE_GEOMETRY,
            self._editor_logic.GetReferenceGeometryImage(),
            self._to_vtk_string_array(segment_ids),
        )
        self._set_label_map_transform_to_volume_transform(label_map)
        return label_map

    @staticmethod
    def _to_vtk_string_array(segment_ids: list[str] | None) -> vtkStringArray | None:
        if not segment_ids:
            return None
        segment_ids_array = vtkStringArray()
        for segment_id in segment_ids:
            segment_ids_array.InsertNextValue(segment_id)
        return segment_ids_array

    def _set_label_map_transform_to_volume_transform(self, label_map: vtkOrientedImageData | None) -> None:
        if not label_map:
            return

        source_image_data = self.get_source_image_data()
        if not source_image_data:
            return

        # Configure modifier label map with the source volume's image to world matrix
        image_to_world = vtkMatrix4x4()
        source_image_data.GetImageToWorldMatrix(image_to_world)
        label_map.SetImageToWorldMatrix(image_to_world)

    def get_mask_label_map(self) -> vtkOrientedImageData | None:
        self._editor_logic.UpdateMaskLabelmap()
        return self._editor_logic.GetMaskLabelmap()

    def get_selected_segment_label_map(self) -> vtkOrientedImageData | None:
        self._editor_logic.UpdateSelectedSegmentLabelmap()
        return self._editor_logic.GetSelectedSegmentLabelmap()

    def _create_editor_node(self, scene: vtkMRMLScene) -> vtkMRMLSegmentEditorNode:
        """
        Create unique editor node for the segmentation
        """
        editor_node = vtkMRMLSegmentEditorNode()
        editor_node.SetName(f"SegmentEditorNode_{id(self)}")
        editor_node.SetSingletonOn()
        return scene.AddNode(editor_node)

    @classmethod
    def _create_editor_logic(
        cls, scene: vtkMRMLScene, editor_node: vtkMRMLSegmentEditorNode
    ) -> vtkSlicerSegmentEditorLogic:
        editor_logic = vtkSlicerSegmentEditorLogic()
        editor_logic.SetMRMLScene(scene)
        editor_logic.SetSegmentEditorNode(editor_node)
        editor_logic.SetSegmentationHistory(None)
        return editor_logic

    @property
    def scene(self) -> vtkMRMLScene:
        return self._scene

    @property
    def editor_node(self) -> vtkMRMLSegmentEditorNode:
        return self._editor_node
