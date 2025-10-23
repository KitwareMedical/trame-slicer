from __future__ import annotations

from abc import ABC, abstractmethod
from weakref import ref

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLLayerDMObjectEventObserverScripted,
    vtkMRMLNode,
    vtkMRMLScene,
    vtkMRMLScriptedModuleNode,
)

from .segment_modifier import ModificationMode, SegmentModifier
from .segmentation_effect_pipeline import SegmentationEffectPipeline


class SegmentationEffect(ABC):
    _effect_type_key = "__SegmentEditorEffectType"

    def __init__(self) -> None:
        self._modifier: SegmentModifier | None = None
        self._modification_mode: ModificationMode = ModificationMode.Add
        self._pipelines: list[ref[SegmentationEffectPipeline]] = []
        self._is_active = False
        self._scene: vtkMRMLScene | None = None
        self._param_node: vtkMRMLScriptedModuleNode | None = None
        self._obs = vtkMRMLLayerDMObjectEventObserverScripted()
        self._obs.SetPythonCallback(self._on_object_event)

    @property
    def modifier(self) -> SegmentModifier:
        return self._modifier

    @property
    def pipelines(self) -> list[ref[SegmentationEffectPipeline]]:
        return self._pipelines

    @property
    def is_active(self) -> bool:
        return self._is_active

    def set_scene(self, scene: vtkMRMLScene):
        self._obs.UpdateObserver(self._scene, scene, vtkMRMLScene.EndCloseEvent)
        self._scene = scene

    def set_modifier(self, modifier: SegmentModifier | None) -> None:
        """
        Set the segment editor of the current pipeline.
        """
        self._modifier = modifier
        self._synchronize_pipelines_modifiers()

    def set_mode(self, mode: ModificationMode):
        self._modification_mode = mode
        self._synchronize_pipelines_modifiers()

    def _synchronize_pipelines_modifiers(self):
        if self._modifier:
            self._modifier.modification_mode = self._modification_mode

    @classmethod
    def get_effect_name(cls):
        module = cls.__module__
        qualname = cls.__qualname__
        return qualname if module in (None, "builtins") else f"{module}.{qualname}"

    def _create_parameter_node(self):
        """
        Create the segment editor effect parameter for the current class.
        By default, the parameter contains the class fully qualified name for creation logic.
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

    def _clear(self):
        self.set_active(False)
        self._pipelines.clear()
        self._param_node = None
        self._modifier = None
        self._is_active = False
