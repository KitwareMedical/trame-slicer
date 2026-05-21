from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from weakref import ref

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLLayerDMObjectEventObserverScripted,
    vtkMRMLNode,
    vtkMRMLScene,
    vtkMRMLScriptedModuleNode,
    vtkMRMLSegmentEditorNode,
)
from undo_stack import Signal

from .segment_modifier import ModificationMode, SegmentModifier

if TYPE_CHECKING:
    from ..core import SegmentationEditor
    from .segmentation_effect_pipeline import SegmentationEffectPipeline


class SegmentationEffect(ABC):
    _effect_type_key = "__SegmentEditorEffectType"
    parameters_changed = Signal()

    def __init__(self) -> None:
        self._modification_mode: ModificationMode = ModificationMode.Add
        self._pipelines: list[ref[SegmentationEffectPipeline]] = []
        self._is_active = False
        self._scene: vtkMRMLScene | None = None
        self._param_node: vtkMRMLScriptedModuleNode | None = None
        self._obs = vtkMRMLLayerDMObjectEventObserverScripted()
        self._obs.SetPythonCallback(self._on_object_event)
        self._editor: SegmentationEditor | None = None

    @property
    def editor(self) -> SegmentationEditor | None:
        return self._editor

    def set_editor(self, editor: SegmentationEditor) -> None:
        self._editor = editor

    @property
    def editor_node(self) -> vtkMRMLSegmentEditorNode | None:
        return self._editor.editor_node if self._editor else None

    @property
    def modifier(self) -> SegmentModifier | None:
        return self._editor.active_segment_modifier if self._editor else None

    @property
    def pipelines(self) -> list[ref[SegmentationEffectPipeline]]:
        return self._pipelines

    @property
    def is_active(self) -> bool:
        return self._is_active

    def set_scene(self, scene: vtkMRMLScene):
        self._obs.UpdateObserver(self._scene, scene, vtkMRMLScene.EndCloseEvent)
        self._scene = scene

    def set_mode(self, mode: ModificationMode):
        self._modification_mode = mode
        self._synchronize_modifier_mode()

    def _synchronize_modifier_mode(self):
        if self.is_active and self.modifier:
            self.modifier.modification_mode = self._modification_mode

    @classmethod
    def get_effect_name(cls):
        module = cls.__module__
        qualname = cls.__qualname__
        return qualname if module in (None, "builtins") else f"{module}.{qualname}"

    def _create_parameter_node(self) -> vtkMRMLScriptedModuleNode:
        """
        Create the segment editor effect parameter node for the current class.
        By default, the node contains the class's fully qualified name for creation logic.
        The effect's save / restore from scene is deactivated by default as creation and management should be handled
        by an instance of the segmentation editor object.

        This method can be overridden to set concrete segment editor default values.

        :return: Newly created instance of the parameter node
        """
        node = vtkMRMLScriptedModuleNode()
        node.SetName(self.get_effect_name() + "_ParameterNode")
        node.SetParameter(self._effect_type_key, self.get_effect_name())
        node.SetSaveWithScene(False)
        return node

    def get_parameter_node(self):
        if self._param_node is None:
            self._param_node = self._create_parameter_node()
            self._obs.UpdateObserver(None, self._param_node)
        return self._param_node

    def is_effect_parameter(self, parameter: vtkMRMLNode) -> bool:
        if not isinstance(parameter, vtkMRMLScriptedModuleNode):
            return False

        return parameter.GetParameter(self._effect_type_key) == self.get_effect_name()

    def activate(self) -> None:
        self.set_active(True)

    def deactivate(self) -> None:
        self.set_active(False)

    def set_active(self, is_active):
        if self._is_active == is_active:
            return
        self._is_active = is_active
        self._synchronize_pipeline_active()
        self._remove_outdated_pipelines()
        self._synchronize_modifier_mode()

    def _synchronize_pipeline_active(self):
        for weak_pipeline in self._pipelines:
            if pipeline := weak_pipeline():
                pipeline.SetActive(self.is_active)

    def _remove_outdated_pipelines(self):
        self._pipelines = [r for r in self._pipelines if r() is not None]

    def create_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        if not self.is_effect_parameter(parameter):
            return None

        if pipeline := self._create_pipeline(view_node, parameter):
            pipeline.SetSegmentationEffect(self)
            self._pipelines.append(ref(pipeline))
            return pipeline

        return None

    @abstractmethod
    def _create_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        pass

    def _on_object_event(self, vtk_object, event_id, _call_data):
        if vtk_object == self._scene and event_id == vtkMRMLScene.EndCloseEvent:
            self._clear()
        elif vtk_object == self._param_node:
            self.parameters_changed.emit()

    def _clear(self):
        self.set_active(False)
        self._pipelines.clear()
        self._param_node = None
        self._is_active = False

    def trigger_pipeline_parameter_change(self, *_):
        with self.parameters_changed.emit_blocked():
            self.get_parameter_node().Modified()
