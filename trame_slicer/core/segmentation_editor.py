from __future__ import annotations

from pathlib import Path

from numpy.typing import NDArray
from slicer import (
    vtkMRMLLabelMapVolumeNode,
    vtkMRMLModelNode,
    vtkMRMLScene,
    vtkMRMLSegmentationNode,
    vtkMRMLVolumeArchetypeStorageNode,
    vtkMRMLVolumeNode,
    vtkSegment,
    vtkSegmentation,
    vtkSlicerSegmentationsModuleLogic,
)
from undo_stack import Signal, SignalContainer, UndoStack
from vtkmodules.vtkCommonDataModel import vtkImageData

from trame_slicer.segmentation import (
    Segmentation,
    SegmentationEffect,
    SegmentationEffectID,
    SegmentationEraseEffect,
    SegmentationOpacityEnum,
    SegmentationPaintEffect,
    SegmentationScissorEffect,
    SegmentModifier,
    SegmentProperties,
)

from .view_manager import ViewManager


class SegmentationEditor(SignalContainer):
    """
    Helper class to activate / deactivate / load / export segmentation.
    """

    segmentation_modified = Signal()
    active_segment_id_changed = Signal(str)
    active_effect_name_changed = Signal(str)
    show_3d_changed = Signal(bool)

    def __init__(
        self,
        scene: vtkMRMLScene,
        logic: vtkSlicerSegmentationsModuleLogic,
        view_manager: ViewManager,
    ) -> None:
        self._logic = logic
        self._view_manager = view_manager
        self._scene = scene

        self._active_effect: SegmentationEffect | None = None
        self._builtin_effects: dict[SegmentationEffectID, type] = {
            SegmentationEffectID.Paint: SegmentationPaintEffect,
            SegmentationEffectID.Erase: SegmentationEraseEffect,
            SegmentationEffectID.Scissors: SegmentationScissorEffect,
        }

        self._active_modifier: SegmentModifier | None = None
        self._undo_stack: UndoStack | None = None
        self._modified_obs = None

    def set_undo_stack(self, undo_stack: UndoStack):
        self._undo_stack = undo_stack
        if self.active_segmentation:
            self.active_segmentation.set_undo_stack(undo_stack)

    @property
    def undo_stack(self) -> UndoStack | None:
        return self._undo_stack

    @property
    def active_segmentation(self) -> Segmentation | None:
        return self._active_modifier.segmentation if self._active_modifier else None

    @property
    def active_segmentation_node(self):
        return self.active_segmentation.segmentation_node if self.active_segmentation else None

    @property
    def active_volume_node(self) -> vtkMRMLVolumeNode | None:
        return self._active_modifier.volume_node if self._active_modifier else None

    @property
    def active_segment_modifier(self) -> SegmentModifier | None:
        return self._active_modifier

    @property
    def active_effect(self) -> SegmentationEffect | None:
        return self._active_effect

    def set_active_segmentation(self, segmentation_node, volume_node):
        segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(volume_node)

        if self._modified_obs is not None:
            self._active_modifier.segmentation_modified.disconnect(self._modified_obs)

        self._active_modifier = SegmentModifier(Segmentation(segmentation_node, volume_node))

        self.active_segmentation.sanitize_active_segmentation()
        self._active_modifier.segmentation_modified.connect(self.segmentation_modified)

        if self._active_effect:
            self._active_effect.modifier = self._active_modifier

        self.set_active_segment_id(self.get_nth_segment_id(0))

        if self._undo_stack:
            self._undo_stack.clear()
            self.active_segmentation.set_undo_stack(self._undo_stack)

        self.deactivate_effect()
        self.trigger_all_signals()

    @staticmethod
    def _initialize_segmentation_node(
        segmentation_node: vtkMRMLSegmentationNode,
    ) -> None:
        segmentation_node.CreateDefaultDisplayNodes()
        segmentation_node.SetDisplayVisibility(True)

    def create_segmentation_node_from_model_node(self, model_node: vtkMRMLModelNode) -> vtkMRMLSegmentationNode:
        segmentation_node = self.create_empty_segmentation_node()
        self._logic.ImportModelToSegmentationNode(model_node, segmentation_node, "")
        segmentation_node.SetName(model_node.GetName())
        return segmentation_node

    def create_segmentation_node_from_labelmap(
        self, labelmap_node: vtkMRMLLabelMapVolumeNode
    ) -> vtkMRMLSegmentationNode:
        segmentation_node = self.create_empty_segmentation_node()
        self._logic.ImportLabelmapToSegmentationNode(labelmap_node, segmentation_node, "")
        segmentation_node.SetName(labelmap_node.GetName())
        return segmentation_node

    def create_empty_segmentation_node(self) -> vtkMRMLSegmentationNode:
        segmentation_node: vtkMRMLSegmentationNode = self._scene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        self._initialize_segmentation_node(segmentation_node)
        return segmentation_node

    def set_active_effect_id(
        self, effect: SegmentationEffectID, view_group: list[int] | None = None
    ) -> SegmentationEffect | None:
        return self.set_active_effect(self._builtin_effects[effect](self._active_modifier), view_group)

    def set_active_effect(
        self,
        effect: SegmentationEffect | None,
        view_group: list[int] | None = None,
    ):
        if self._active_effect == effect:
            return None

        if self._active_effect:
            self._active_effect.deactivate()

        self._active_effect = effect

        if self._active_effect:
            self._active_effect.activate(self._view_manager.get_views(view_group))

        self.active_effect_name_changed(self._active_effect.class_name() if self._active_effect else "")
        return self._active_effect

    @property
    def active_effect_name(self) -> str:
        return self._active_effect.class_name() if self._active_effect else ""

    def deactivate_effect(self):
        self.set_active_effect(None)

    def get_segment_ids(self) -> list[str]:
        return self.active_segmentation.get_segment_ids() if self.active_segmentation else []

    def get_segment_names(self) -> list[str]:
        return self.active_segmentation.get_segment_names() if self.active_segmentation else []

    def get_all_segment_properties(self) -> dict[str, SegmentProperties]:
        if not self.active_segmentation:
            return {}
        return {s_id: self.get_segment_properties(s_id) for s_id in self.get_segment_ids()}

    def get_segment_properties(self, segment_id):
        if not self.active_segmentation:
            return None
        return self.active_segmentation.get_segment_properties(segment_id)

    def set_segment_properties(self, segment_id, segment_properties: SegmentProperties):
        if not self.active_segmentation:
            return
        self.active_segmentation.set_segment_properties(segment_id, segment_properties)

    @property
    def n_segments(self) -> int:
        return self.active_segmentation.n_segments if self.active_segmentation else 0

    def get_nth_segment(self, i_segment: int) -> vtkSegment | None:
        return self.active_segmentation.get_nth_segment(i_segment) if self.active_segmentation else None

    def get_nth_segment_id(self, i_segment: int) -> str:
        return self.active_segmentation.get_nth_segment_id(i_segment) if self.active_segmentation else ""

    def get_segment(self, segment_id: str) -> vtkSegment | None:
        return self.active_segmentation.get_segment(segment_id) if self.active_segmentation else None

    def add_empty_segment(
        self,
        *,
        segment_id="",
        segment_name="",
        segment_color: list[float] | None = None,
        segment_value: int | None = None,
    ) -> str:
        if not self.active_segmentation:
            return ""

        segment_id = self.active_segmentation.add_empty_segment(
            segment_id=segment_id,
            segment_name=segment_name,
            segment_color=segment_color,
            segment_value=segment_value,
        )
        self.set_active_segment_id(segment_id)
        return segment_id

    def remove_segment(self, segment_id):
        segment_ids = self.get_segment_ids()
        if not self.active_segmentation or segment_id not in segment_ids:
            return

        next_index = segment_ids.index(segment_id) - 1
        self.active_segmentation.remove_segment(segment_id)
        self.set_active_segment_id(segment_ids[max(next_index, 0)])

    def get_active_segment_id(self) -> str:
        return self._active_modifier.active_segment_id if self._active_modifier else ""

    def set_active_segment_id(self, segment_id):
        if not self._active_modifier:
            return

        self._active_modifier.active_segment_id = segment_id
        self.active_segment_id_changed(self.active_segment_id)
        if not self.active_segment_id:
            self.deactivate_effect()

    @property
    def active_segment_id(self) -> str:
        if not self._active_modifier:
            return ""
        return self._active_modifier.active_segment_id

    def get_segment_labelmap(
        self, segment_id: str, *, as_numpy_array: bool = False, do_sanitize=True
    ) -> vtkImageData | NDArray | None:
        return (
            self.active_segmentation.get_segment_labelmap(
                segment_id, as_numpy_array=as_numpy_array, do_sanitize=do_sanitize
            )
            if self.active_segmentation
            else None
        )

    def export_segmentation_to_labelmap(
        self,
        segmentation_node: vtkMRMLSegmentationNode,
        labelmap: vtkMRMLLabelMapVolumeNode = None,
    ) -> vtkMRMLLabelMapVolumeNode:
        labelmap = labelmap or self._scene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        self._logic.ExportAllSegmentsToLabelmapNode(
            segmentation_node, labelmap, vtkSegmentation.EXTENT_REFERENCE_GEOMETRY
        )
        return labelmap

    def export_segmentation_to_file(self, segmentation_node: vtkMRMLSegmentationNode, file_path: str) -> None:
        from .io_manager import IOManager

        labelmap = self.export_segmentation_to_labelmap(segmentation_node)
        try:
            IOManager.write_node(
                labelmap,
                file_path,
                vtkMRMLVolumeArchetypeStorageNode,
                do_convert_from_slicer_coord=True,
            )
        finally:
            self._scene.RemoveNode(labelmap)

    def export_segmentation_to_models(self, segmentation_node: vtkMRMLSegmentationNode, folder_item_id: int) -> None:
        self._logic.ExportAllSegmentsToModels(segmentation_node, folder_item_id)

    def export_segmentation_to_stl(
        self,
        segmentation_node: vtkMRMLSegmentationNode,
        out_folder: str,
        segment_ids: list[str] | None = None,
    ) -> None:
        self._logic.ExportSegmentsClosedSurfaceRepresentationToFiles(out_folder, segmentation_node, segment_ids)

    def load_segmentation_from_file(self, segmentation_file: str) -> vtkMRMLSegmentationNode | None:
        segmentation_file = Path(segmentation_file).resolve()
        if not segmentation_file.is_file():
            return None

        node_name = segmentation_file.stem
        return self._logic.LoadSegmentationFromFile(segmentation_file.as_posix(), True, node_name)

    def set_surface_representation_enabled(self, is_enabled: bool) -> None:
        if not self.active_segmentation:
            return
        self.active_segmentation.set_surface_representation_enabled(is_enabled)
        self.show_3d_changed(is_enabled)

    def is_surface_representation_enabled(self) -> bool:
        return self.active_segmentation.is_surface_representation_enabled() if self.active_segmentation else False

    def show_3d(self, show_3d: bool):
        self.set_surface_representation_enabled(show_3d)

    def is_3d_shown(self):
        return self.is_surface_representation_enabled()

    def create_modifier_labelmap(self) -> vtkImageData | None:
        return self.active_segmentation.create_modifier_labelmap() if self.active_segmentation else None

    def apply_labelmap(self, labelmap) -> None:
        if not self.active_segment_modifier:
            return
        self.active_segment_modifier.apply_labelmap(labelmap)

    def apply_polydata_world(self, poly_world) -> None:
        if not self.active_segment_modifier:
            return
        self.active_segment_modifier.apply_polydata_world(poly_world)

    def trigger_all_signals(self):
        self.active_segment_id_changed(self.active_segment_id)
        self.active_effect_name_changed(self.active_effect_name)
        self.show_3d_changed(self.is_3d_shown())
        self.segmentation_modified()

    def set_segment_visibility(self, segment_id, visibility: bool) -> None:
        if not self.active_segmentation:
            return None
        return self.active_segmentation.set_segment_visibility(segment_id, visibility)

    def get_segment_visibility(self, segment_id) -> bool | None:
        if not self.active_segmentation:
            return None
        return self.active_segmentation.get_segment_visibility(segment_id)

    def set_opacity_mode(self, opacity_mode: SegmentationOpacityEnum) -> None:
        if not self.active_segmentation:
            return
        self.active_segmentation.set_opacity_mode(opacity_mode)

    def get_opacity_mode(self) -> SegmentationOpacityEnum | None:
        if not self.active_segmentation:
            return None
        return self.active_segmentation.get_opacity_mode()

    def get_2d_opacity(self) -> float | None:
        if not self.active_segmentation:
            return None
        return self.active_segmentation.get_2d_opacity()

    def set_2d_opacity(self, opacity: float) -> None:
        if not self.active_segmentation:
            return
        self.active_segmentation.set_2d_opacity(opacity)

    def get_3d_opacity(self) -> float | None:
        if not self.active_segmentation:
            return None
        return self.active_segmentation.get_3d_opacity()

    def set_3d_opacity(self, opacity: float) -> None:
        if not self.active_segmentation:
            return
        self.active_segmentation.set_3d_opacity(opacity)
