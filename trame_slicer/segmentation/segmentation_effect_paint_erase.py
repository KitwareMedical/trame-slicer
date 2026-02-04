from __future__ import annotations

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLModelNode,
    vtkMRMLNode,
    vtkMRMLSliceNode,
    vtkMRMLViewNode,
)
from undo_stack import Signal

from trame_slicer.utils import create_scripted_module_dataclass_proxy

from .paint_effect_parameters import BrushDiameterMode, PaintEffectParameters
from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_paint_pipeline import (
    SegmentationPaintPipeline2D,
    SegmentationPaintPipeline3D,
)


class SegmentationEffectPaintErase(SegmentationEffect):
    on_brush_diameter_changed = Signal(int)

    def __init__(self, mode: ModificationMode) -> None:
        super().__init__()
        self.set_mode(mode)

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
        proxy = self._get_proxy()
        if proxy.brush_model_node is None:
            proxy.brush_model_node = self._create_model_node("BrushModel")
            proxy.paint_feedback_model_node = self._create_model_node("FeedbackModel")
            proxy.paint_feedback_model_node.GetDisplayNode().SetOpacity(0.5)

        # Toggle visibility depending on active
        proxy.brush_model_node.SetDisplayVisibility(self.is_active)
        proxy.paint_feedback_model_node.SetDisplayVisibility(self.is_active)

    def _get_proxy(self) -> PaintEffectParameters:
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
        proxy = self._get_proxy()
        proxy.use_sphere_brush = use_sphere_brush

    def set_brush_diameter(self, diameter: float, diameter_mode: BrushDiameterMode):
        proxy = self._get_proxy()
        proxy.brush_diameter = diameter
        proxy.brush_diameter_mode = diameter_mode
        self.on_brush_diameter_changed(diameter)

    def increase_brush_size(self, *_args, **_kwargs):
        proxy = self._get_proxy()
        proxy.brush_diameter *= 1.1
        self.on_brush_diameter_changed(proxy.brush_diameter)

    def decrease_brush_size(self, *_args, **_kwargs):
        proxy = self._get_proxy()
        proxy.brush_diameter /= 1.1
        self.on_brush_diameter_changed(proxy.brush_diameter)

    def is_sphere_brush(self) -> bool:
        return self._get_proxy().use_sphere_brush

    def get_brush_diameter(self) -> float:
        return self._get_proxy().brush_diameter

    def get_brush_diameter_mode(self) -> BrushDiameterMode:
        return self._get_proxy().brush_diameter_mode


class SegmentationEffectPaint(SegmentationEffectPaintErase):
    def __init__(self) -> None:
        super().__init__(ModificationMode.Add)


class SegmentationEffectErase(SegmentationEffectPaintErase):
    def __init__(self) -> None:
        super().__init__(ModificationMode.Remove)
