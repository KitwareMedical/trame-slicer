from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from numpy.typing import NDArray
from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLLabelMapVolumeNode,
    vtkMRMLLayerDMPipelineFactory,
    vtkMRMLLayerDMPipelineScriptedCreator,
    vtkMRMLModelNode,
    vtkMRMLNode,
    vtkMRMLScene,
    vtkMRMLScriptedModuleNode,
    vtkMRMLSegmentationNode,
    vtkMRMLSegmentEditorNode,
    vtkMRMLVolumeArchetypeStorageNode,
    vtkMRMLVolumeNode,
    vtkSegment,
    vtkSegmentation,
    vtkSlicerSegmentationsModuleLogic,
    vtkSlicerSegmentEditorLogic,
)
from undo_stack import Signal, SignalContainer, UndoStack
from vtkmodules.vtkCommonDataModel import vtkImageData

from trame_slicer.segmentation import (
    Segmentation,
    SegmentationDisplay,
    SegmentationEffect,
    SegmentationEffectErase,
    SegmentationEffectNoTool,
    SegmentationEffectPaint,
    SegmentationEffectPipeline,
    SegmentationEffectScissors,
    SegmentModifier,
    SegmentProperties,
)
from trame_slicer.utils import ensure_node_in_scene

if TYPE_CHECKING:
    from trame_slicer.core import ViewManager


class SegmentationEditor(SignalContainer):
    """
    Class responsible for editing the segmentation.
    Meant to be used by the application to activate / deactivate segmentation effects.
    """

    builtin_effects: ClassVar[list[type[SegmentationEffect]]] = [
        SegmentationEffectNoTool,
        SegmentationEffectPaint,
        SegmentationEffectErase,
        SegmentationEffectScissors,
    ]

    segmentation_modified = Signal()
    segmentation_display_modified = Signal()
    active_segment_id_changed = Signal(str)
    active_effect_name_changed = Signal(str)
    show_3d_changed = Signal(bool)

    def __init__(
        self,
        scene: vtkMRMLScene,
        logic: vtkSlicerSegmentationsModuleLogic,
        view_manager: ViewManager,
    ) -> None:
        if SegmentationEffectNoTool not in self.builtin_effects:
            _error_msg = "The no tool effect is expected to be in the builtin effects to correctly deactivate the segmentation effects."
            raise RuntimeError(_error_msg)

        self._logic = logic

        self._scene = scene
        self._view_manager = view_manager
        self._editor_node = self._create_editor_node()

        # Configure segment editor logic (Set maximum of states to undo / redo to 0 to cherry pick undo / redo behavior)
        self._editor_logic = vtkSlicerSegmentEditorLogic()
        self._editor_logic.SetMRMLScene(scene)
        self._editor_logic.SetSegmentEditorNode(self._editor_node)
        self._editor_logic.SetSegmentationHistory(None)

        self._active_effect: SegmentationEffect | None = None
        self._active_effect_class_name: str = SegmentationEffectNoTool.get_effect_name()

        self._effects: dict[str, SegmentationEffect] = {}
        self._effect_parameters: dict[str, vtkMRMLScriptedModuleNode] = {}
        self._active_modifier: SegmentModifier | None = None
        self._undo_stack: UndoStack | None = None
        self._modified_obs = None
        self._do_show_3d = False

        for effect in self.builtin_effects:
            self.register_effect_type(effect)

        # Register pipeline creator
        self._pipeline_creator = vtkMRMLLayerDMPipelineScriptedCreator()
        self._pipeline_creator.SetPythonCallback(self._try_create_effect_pipeline)
        vtkMRMLLayerDMPipelineFactory.GetInstance().AddPipelineCreator(self._pipeline_creator)
        self.segmentation_modified.connect(self._on_segmentation_modified)

        # Observe scene close event to clear undo stack
        self._scene.AddObserver(vtkMRMLScene.EndCloseEvent, self._on_scene_close)

    def _create_editor_node(self):
        """
        Create unique editor node for the segmentation editor.
        """
        editor_node = vtkMRMLSegmentEditorNode()
        editor_node.SetName(f"SegmentEditorNode_{id(self)}")
        editor_node.SetSingletonOn()
        self._scene.AddNode(editor_node)
        return editor_node

    @property
    def editor_logic(self) -> vtkSlicerSegmentEditorLogic:
        return self._editor_logic

    @property
    def editor_node(self) -> vtkMRMLSegmentEditorNode:
        return self._editor_node

    def is_effect_type_registered(self, effect_type: type[SegmentationEffect]) -> bool:
        return effect_type.get_effect_name() in self._effects

    def register_effect_type(self, effect_type: type[SegmentationEffect]) -> None:
        """
        Registers the input segment editor effect pipeline for the segmentation editor.
        :param effect_type:
        :return:
        """
        if self.is_effect_type_registered(effect_type):
            return

        effect = effect_type()
        effect.set_scene(self._scene)
        self._effects[effect_type.get_effect_name()] = effect

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
    def active_segmentation_display(self) -> SegmentationDisplay | None:
        return self.active_segmentation.get_display() if self.active_segmentation else None

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

        self._active_modifier = SegmentModifier(
            Segmentation(segmentation_node, volume_node, editor_logic=self._editor_logic, undo_stack=self.undo_stack)
        )

        self._active_modifier.segmentation_modified.connect(self.segmentation_modified)

        if self._active_effect:
            self._active_effect.set_modifier(self._active_modifier)

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

    def set_active_effect_type(self, effect_type: type[SegmentationEffect]) -> SegmentationEffect | None:
        self.register_effect_type(effect_type)
        return self.set_active_effect_name(effect_type.get_effect_name())

    def set_active_effect_name(self, effect_id: str) -> SegmentationEffect | None:
        if effect_id not in self._effects:
            _warn_msg = f"Unknown effect id : {effect_id}"
            logging.warning(_warn_msg)
            return None

        effect = self._effects[effect_id]
        self.set_active_effect(effect)
        return effect

    def set_active_effect(self, effect: SegmentationEffect | None):
        if self._active_effect == effect:
            return None

        if self._active_effect:
            self._active_effect.set_modifier(None)
            self._active_effect.deactivate()

        self._add_effect_parameters_to_scene(effect)
        self._active_effect = effect

        if self._active_effect:
            self._active_effect.set_modifier(self._active_modifier)
            self._active_effect.activate()

        self.active_effect_name_changed(self.active_effect_name)
        return self._active_effect

    @property
    def active_effect_name(self) -> str:
        return self.get_active_effect_name()

    def get_active_effect_name(self) -> str:
        return self._active_effect.get_effect_name() if self._active_effect else ""

    def deactivate_effect(self):
        self.set_active_effect_type(SegmentationEffectNoTool)

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

    def get_segment_labelmap(self, segment_id: str, *, as_numpy_array: bool = False) -> vtkImageData | NDArray | None:
        return (
            self.active_segmentation.get_segment_labelmap(segment_id, as_numpy_array=as_numpy_array)
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
        if self._do_show_3d == is_enabled:
            return
        self._do_show_3d = is_enabled
        self._ensure_active_segmentation_surface_repr_consistency()
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
        if not self.active_segmentation_display:
            return None
        return self.active_segmentation_display.set_segment_visibility(segment_id, visibility)

    def get_segment_visibility(self, segment_id) -> bool | None:
        if not self.active_segmentation_display:
            return None
        return self.active_segmentation_display.get_segment_visibility(segment_id)

    def get_effect_parameter_node(
        self, effect: SegmentationEffect | type[SegmentationEffect]
    ) -> vtkMRMLScriptedModuleNode:
        """
        returns segmentation effect parameter node as used by this segment editor.
        When passing effect types as inputs, this method will ensure the effect has been registered.
        If the parameter node doesn't exist in the current scene, the parameter node will be added automatically.
        """
        if inspect.isclass(effect):
            self.register_effect_type(effect)
            effect = self._effects[effect.get_effect_name()]
        return self._add_effect_parameters_to_scene(effect)

    def _add_effect_parameters_to_scene(self, effect: SegmentationEffect) -> vtkMRMLScriptedModuleNode:
        """
        Create the default effect parameters linked to the input effect id and add it the current list of tracked
        segmentation effect parameters.

        Created parameter is added to the scene if not present (scene clear / first instantiation).
        Adding the parameter to the scene will trigger the pipeline registration if needed.

        :param effect: Segment editor effect instance.
        :return: Instance of the created parameter.
        """
        effect_name = effect.get_effect_name()
        if effect_name not in self._effect_parameters:
            self._effect_parameters[effect_name] = effect.get_parameter_node()

        return ensure_node_in_scene(self._effect_parameters[effect_name], self._scene)

    def _try_create_effect_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, parameter_node: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        """
        Try to create the segment editor effect pipeline given the input view node and parameter node.
        Only creates the pipelines for effects whose parameters are currently managed by the segmentation editor.

        :param view_node:
        :param parameter_node:
        :return:
        """
        if parameter_node not in self._effect_parameters.values():
            return None

        for effect_type in self._effects.values():
            if pipeline := effect_type.create_pipeline(view_node, parameter_node):
                pipeline.SetView(self._view_manager.get_view(view_node))
                return pipeline

        return None

    def _on_segmentation_modified(self):
        self._ensure_active_segmentation_surface_repr_consistency()

    def _ensure_active_segmentation_surface_repr_consistency(self):
        # make sure the current segmentation surface representation matches the show_3d state
        if not self.active_segmentation:
            return

        if self._do_show_3d != self.is_surface_representation_enabled():
            self.active_segmentation.set_surface_representation_enabled(self._do_show_3d)

    def _on_scene_close(self, *_):
        self.clear()

    def clear(self):
        self._clear_undo_stack()
        self.deactivate_effect()
        self._active_modifier = None
        self._modified_obs = None
        self._effect_parameters.clear()
        self.trigger_all_signals()

    def _clear_undo_stack(self):
        if not self.undo_stack:
            return
        self.undo_stack.clear()
