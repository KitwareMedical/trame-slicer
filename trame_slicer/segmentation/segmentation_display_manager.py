from __future__ import annotations

from typing import TYPE_CHECKING
from weakref import ref

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLLayerDMPipelineFactory,
    vtkMRMLLayerDMPipelineScriptedCreator,
    vtkMRMLNode,
    vtkMRMLScene,
    vtkMRMLSegmentEditorNode,
    vtkSlicerSegmentationsModuleLogic,
)
from undo_stack import Signal, SignalContainer

from ..utils import ensure_node_in_scene
from .segmentation import Segmentation
from .segmentation_display import SegmentationDisplay
from .segmentation_threshold_mask_pipeline import SegmentationThresholdMaskPipeline

if TYPE_CHECKING:
    from trame_slicer.core import SegmentationEditor, ViewManager


class SegmentationDisplayManager(SignalContainer):
    show_3d_changed = Signal(bool)
    parameter_changed = Signal()

    def __init__(
        self,
        scene: vtkMRMLScene,
        logic: vtkSlicerSegmentationsModuleLogic,
        segmentation_editor: SegmentationEditor,
        view_manager: ViewManager,
    ) -> None:
        self._logic = logic

        self._scene = scene
        self._view_manager = view_manager
        self._segmentation_editor = segmentation_editor

        self._do_show_3d = False
        self._threshold_mask_color: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.5)

        self._pipelines: list[ref[SegmentationThresholdMaskPipeline]] = []
        self._threshold_mask_parameter_node = None
        self._threshold_mask_pipeline_creator = vtkMRMLLayerDMPipelineScriptedCreator()
        self._threshold_mask_pipeline_creator.SetPythonCallback(self._try_create_threshold_mask_pipeline)
        vtkMRMLLayerDMPipelineFactory.GetInstance().AddPipelineCreator(self._threshold_mask_pipeline_creator)

    @property
    def active_segmentation(self) -> Segmentation | None:
        return self._segmentation_editor.active_segmentation

    @property
    def active_segmentation_display(self) -> SegmentationDisplay | None:
        return self._segmentation_editor.active_segmentation_display

    @property
    def editor_node(self) -> vtkMRMLSegmentEditorNode:
        return self._segmentation_editor.editor_node

    @property
    def pipelines(self) -> list[ref[SegmentationThresholdMaskPipeline]]:
        return self._pipelines

    def set_surface_representation_enabled(self, is_enabled: bool) -> None:
        if self._do_show_3d == is_enabled:
            return
        self._do_show_3d = is_enabled
        self.ensure_active_segmentation_surface_repr_consistency()
        self.show_3d_changed(is_enabled)
        self.parameter_changed()

    def ensure_active_segmentation_surface_repr_consistency(self):
        # make sure the current segmentation surface representation matches the show_3d state
        if not self.active_segmentation:
            return

        if self._do_show_3d != self.is_surface_representation_enabled():
            self.active_segmentation.set_surface_representation_enabled(self._do_show_3d)

    def is_surface_representation_enabled(self) -> bool:
        return self.active_segmentation.is_surface_representation_enabled() if self.active_segmentation else False

    def show_3d(self, show_3d: bool):
        self.set_surface_representation_enabled(show_3d)

    def is_3d_shown(self):
        return self.is_surface_representation_enabled()

    def set_segment_visibility(self, segment_id: str, visibility: bool) -> None:
        if not self.active_segmentation_display:
            return None
        return self.active_segmentation_display.set_segment_visibility(segment_id, visibility)

    def get_segment_visibility(self, segment_id: str) -> bool | None:
        if not self.active_segmentation_display:
            return None
        return self.active_segmentation_display.get_segment_visibility(segment_id)

    def get_source_volume_intensity_mask(self) -> bool:
        return self.editor_node.GetSourceVolumeIntensityMask()

    def set_source_volume_intensity_mask(self, use_mask: bool):
        self.editor_node.SetSourceVolumeIntensityMask(use_mask)

    def get_source_volume_intensity_mask_range(self) -> tuple[float, float]:
        return self.editor_node.GetSourceVolumeIntensityMaskRange()

    def set_source_volume_intensity_mask_range(self, low: float, high: float):
        self.editor_node.SetSourceVolumeIntensityMaskRange(low, high)
        self._update_pipelines()

    def create_threshold_mask_pipeline_parameter_node(self):
        if self._threshold_mask_parameter_node is None:
            self._threshold_mask_parameter_node = SegmentationThresholdMaskPipeline.CreateParameterNode()
        ensure_node_in_scene(self._threshold_mask_parameter_node, self._scene)

    def _try_create_threshold_mask_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, parameter_node: vtkMRMLNode
    ) -> SegmentationThresholdMaskPipeline | None:
        if parameter_node != self._threshold_mask_parameter_node:
            return None
        pipeline = SegmentationThresholdMaskPipeline.TryCreatePipeline(view_node, parameter_node, self)
        if pipeline is not None:
            self._pipelines.append(ref(pipeline))
            pipeline.SetView(self._view_manager.get_view(view_node))

        return pipeline

    def set_threshold_mask_visibility(self, visibility: bool):
        for weak_pipeline in self._pipelines:
            if pipeline := weak_pipeline():
                pipeline.SetActive(visibility)

    def get_threshold_mask_color(self) -> tuple[float, float, float, float]:
        return self._threshold_mask_color

    def set_threshold_mask_color(self, r: float, g: float, b: float, a: float = 0.5):
        self._threshold_mask_color = (r, g, b, a)
        self._update_pipelines()

    def _update_pipelines(self):
        for weak_pipeline in self._pipelines:
            if pipeline := weak_pipeline():
                pipeline.RequestRender()
