from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import (
    SegmentationEffectErase,
    SegmentationEffectPaint,
)

from ...ui import PaintEffectState
from .base_segmentation_logic import U
from .brush_effect_logic import BrushEffectLogic


class PaintEraseEffectLogic(BrushEffectLogic[PaintEffectState, U]):
    def __init__(self, server: Server, slicer_app: SlicerApp, effect_type: type[U]):
        super().__init__(server, slicer_app, PaintEffectState, effect_type)


class PaintEffectLogic(PaintEraseEffectLogic[SegmentationEffectPaint]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentationEffectPaint)


class EraseEffectLogic(PaintEraseEffectLogic[SegmentationEffectErase]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, SegmentationEffectErase)
