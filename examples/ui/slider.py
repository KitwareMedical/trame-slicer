from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VRangeSlider, VSlider


@dataclass
class SliderState:
    min_value: float = 0
    max_value: float = 1
    value: float = 0.5
    step: float = 1e-6
    is_reversed: bool = False


@dataclass
class RangeSliderState:
    min_value: float = 0
    max_value: float = 1
    value: list[float] = field(default_factory=lambda: [0.0, 0.5])
    step: float = 1e-6
    is_reversed: bool = False


class Slider(VSlider):
    def __init__(self, typed_state: TypedState[SliderState], **kwargs):
        super().__init__(
            min=(typed_state.name.min_value,),
            max=(typed_state.name.max_value,),
            v_model=(typed_state.name.value,),
            step=(typed_state.name.step,),
            is_reversed=(typed_state.name.is_reversed,),
            hide_details=True,
            **kwargs,
        )


class RangeSlider(VRangeSlider):
    def __init__(self, typed_state: TypedState[RangeSliderState], **kwargs):
        super().__init__(
            min=(typed_state.name.min_value,),
            max=(typed_state.name.max_value,),
            v_model=(typed_state.name.value,),
            step=(typed_state.name.step,),
            is_reversed=(typed_state.name.is_reversed,),
            hide_details=True,
            **kwargs,
        )
