from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from slicer import vtkMRMLModelNode


class BrushShape(Enum):
    Sphere = 0
    Cylinder = 1


class BrushDiameterMode(Enum):
    Absolute = auto()
    ScreenRelative = auto()


@dataclass
class PaintEffectParameters:
    brush_diameter: float = 6.0
    brush_diameter_mode: BrushDiameterMode = BrushDiameterMode.ScreenRelative
    use_sphere_brush: bool = False
    brush_model_node: vtkMRMLModelNode | None = None
    paint_feedback_model_node: vtkMRMLModelNode | None = None
