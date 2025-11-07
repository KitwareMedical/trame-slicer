from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VContainer, VIcon, VRow
from undo_stack import Signal

from ..slider import RangeSlider, RangeSliderState


@dataclass
class ThresholdState:
    threshold_slider: RangeSliderState = field(default_factory=RangeSliderState)


class ThresholdEffectUI(VContainer):
    auto_threshold_clicked = Signal()
    apply_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(classes="fill-width", **kwargs)
        self._typed_state = TypedState(self.state, ThresholdState)

        with self:
            with VRow(classes="align-center"):
                VIcon("mdi-arrow-left-right", classes="mr-2")
                RangeSlider(typed_state=self._typed_state.get_sub_state(self._typed_state.name.threshold_slider))
            with VRow():
                VBtn("Auto threshold", prepend_icon="mdi-auto-mode", block=True, click=self.auto_threshold_clicked)
            with VRow():
                VBtn("Apply", prepend_icon="mdi-check-outline", block=True, click=self.apply_clicked)
