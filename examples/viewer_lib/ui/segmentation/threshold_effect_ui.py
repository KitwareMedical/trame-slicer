from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import Template, VBtn
from undo_stack import Signal

from ..control_button import ControlButton
from ..flex_container import FlexContainer
from ..slider import RangeSlider, RangeSliderState
from ..text_components import Text


@dataclass
class ThresholdState:
    threshold_slider: RangeSliderState = field(default_factory=RangeSliderState)


class ThresholdEffectUI(FlexContainer):
    auto_threshold_clicked = Signal()
    apply_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, ThresholdState)

        with self:
            Text("Threshold range", subtitle=True)
            with (
                RangeSlider(typed_state=self._typed_state.get_sub_state(self._typed_state.name.threshold_slider)),
                Template(v_slot_append=True),
            ):
                ControlButton(name="Auto range", icon="mdi-refresh-auto", click=self.auto_threshold_clicked)

            with FlexContainer(align="end", classes="mt-2"):
                VBtn(text="Apply", prepend_icon="mdi-check", variant="tonal", click=self.apply_clicked)
