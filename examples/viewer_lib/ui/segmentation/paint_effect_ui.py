from dataclasses import dataclass

from trame_server.utils.typed_state import TypedState

from trame_slicer.ui import SliderState

from ..flex_container import FlexContainer
from .brush_parameters_ui import BrushParametersState, BrushParametersUI


@dataclass
class PaintEffectState(BrushParametersState):
    pass


class PaintEffectUI(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, PaintEffectState)
        TypedState.from_dataclass(
            self._typed_state.data.brush_diameter_slider, SliderState(min_value=1, max_value=30, step=1, value=5)
        )

        with self:
            BrushParametersUI(self._typed_state)
