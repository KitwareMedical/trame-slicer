from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLModelNode,
    vtkMRMLNode,
    vtkMRMLSliceNode,
    vtkMRMLViewNode,
)

from trame_slicer.utils import create_scripted_module_dataclass_proxy

from .paint_effect_parameters import PaintEffectParameters
from .segment_modifier import ModificationMode
from .segmentation_effect import SegmentationEffect
from .segmentation_effect_pipeline import SegmentationEffectPipeline
from .segmentation_paint_pipeline import (
    SegmentationPaintPipeline2D,
    SegmentationPaintPipeline3D,
)


class _SegmentationPaintEraseEffect(SegmentationEffect):
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
        proxy = create_scripted_module_dataclass_proxy(PaintEffectParameters, self._param_node, self._scene)
        if proxy.brush_model_node is None:
            proxy.brush_model_node = self._create_model_node("BrushModel")
            proxy.paint_feedback_model_node = self._create_model_node("FeedbackModel")
            proxy.paint_feedback_model_node.GetDisplayNode().SetOpacity(0.5)

        # Toggle visibility depending on active
        proxy.brush_model_node.SetDisplayVisibility(self.is_active)
        proxy.paint_feedback_model_node.SetDisplayVisibility(self.is_active)

    def _create_pipeline(
        self, view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
    ) -> SegmentationEffectPipeline | None:
        if isinstance(view_node, vtkMRMLSliceNode):
            return SegmentationPaintPipeline2D()
        if isinstance(view_node, vtkMRMLViewNode):
            return SegmentationPaintPipeline3D()
        return None


class SegmentationEffectPaint(_SegmentationPaintEraseEffect):
    def __init__(self) -> None:
        super().__init__(ModificationMode.Add)


class SegmentationEffectErase(_SegmentationPaintEraseEffect):
    def __init__(self) -> None:
        super().__init__(ModificationMode.Remove)
