from __future__ import annotations

from abc import ABC, abstractmethod

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLModelNode,
    vtkMRMLNode,
    vtkMRMLSliceNode,
    vtkMRMLViewNode,
)
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData

from trame_slicer.utils import create_scripted_module_dataclass_proxy

from .paint_effect_parameters import BrushDiameterMode, PaintEffectParameters
from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_paint_pipeline import (
    SegmentationPaintPipeline2D,
    SegmentationPaintPipeline3D,
)


class AbstractSegmentationEffectBrush(SegmentationEffect, ABC):
    """Abstract class for segmentation effect implementing a brush behavior in views"""

    def __init__(self, mode: ModificationMode) -> None:
        super().__init__()
        self.set_mode(mode)
        self._default_brush_multiplier_ratio = 1.1

    def _create_model_node(self, name):
        model_node = vtkMRMLModelNode()
        model_node.SetSaveWithScene(False)
        model_node.SetHideFromEditors(True)
        model_node.SetName(self.get_effect_name() + f"_{name}")

        self._scene.AddNode(model_node)
        model_node.CreateDefaultDisplayNodes()
        model_node.GetDisplayNode().SetVisibility2D(True)
        model_node.SetSelectable(False)
        return model_node

    def set_active(self, is_active):
        super().set_active(is_active)
        self._refresh_model_nodes()

    def _refresh_model_nodes(self):
        if not self._param_node:
            return

        # Make sure nodes are present in the scene
        paint_parameters = self._get_paint_parameters()
        if paint_parameters.brush_model_node is None:
            paint_parameters.brush_model_node = self._create_model_node("BrushModel")
            paint_parameters.paint_feedback_model_node = self._create_model_node("FeedbackModel")
            paint_parameters.paint_feedback_model_node.GetDisplayNode().SetOpacity(0.5)

        # Toggle visibility depending on active
        paint_parameters.brush_model_node.SetDisplayVisibility(self.is_active)
        paint_parameters.paint_feedback_model_node.SetDisplayVisibility(self.is_active)

    def _get_paint_parameters(self) -> PaintEffectParameters:
        return create_scripted_module_dataclass_proxy(PaintEffectParameters, self._param_node, self._scene)

    def _create_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        if isinstance(view_node, vtkMRMLSliceNode):
            return SegmentationPaintPipeline2D()
        if isinstance(view_node, vtkMRMLViewNode):
            return SegmentationPaintPipeline3D()
        return None

    def set_use_sphere_brush(self, use_sphere_brush):
        paint_parameters = self._get_paint_parameters()
        paint_parameters.use_sphere_brush = use_sphere_brush

    def set_brush_diameter(self, diameter: float, diameter_mode: BrushDiameterMode | None = None):
        paint_parameters = self._get_paint_parameters()
        paint_parameters.brush_diameter = diameter
        if diameter_mode is not None:
            paint_parameters.brush_diameter_mode = diameter_mode

    def increase_brush_size(self, increase_ratio: float | None = None):
        increase_ratio = increase_ratio or self._default_brush_multiplier_ratio
        paint_parameters = self._get_paint_parameters()
        paint_parameters.brush_diameter *= increase_ratio

    def decrease_brush_size(self, decrease_ratio: float | None = None):
        decrease_ratio = decrease_ratio or self._default_brush_multiplier_ratio
        paint_parameters = self._get_paint_parameters()
        paint_parameters.brush_diameter /= decrease_ratio

    def is_sphere_brush(self) -> bool:
        return self._get_paint_parameters().use_sphere_brush

    def get_brush_diameter(self) -> float:
        return self._get_paint_parameters().brush_diameter

    def get_brush_diameter_mode(self) -> BrushDiameterMode:
        return self._get_paint_parameters().brush_diameter_mode

    @abstractmethod
    def paint_glyph_at_world_coordinates(self, polydata: vtkPolyData, paint_coordinates_world: vtkPoints):
        pass
