from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VCheckbox, VIcon, VSpacer

from trame_slicer.ui import RangeSlider, RangeSliderState

from ..flex_container import FlexContainer
from ..text_components import Text


@dataclass
class VolumeIntensityRangeMaskState:
    threshold_slider: RangeSliderState = field(default_factory=RangeSliderState)
    is_visible: bool = False
    is_enabled: bool = False


class VolumeIntensityRangeMaskUI(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, VolumeIntensityRangeMaskState)

        with self:
            Text("Volume intensity range mask")

            with FlexContainer(row=True):
                VCheckbox(
                    v_model=(self._typed_state.name.is_enabled,),
                    label="Enable mask",
                    hide_details=True,
                    density="compact",
                )
                VSpacer()

                VIcon(
                    classes="mr-3",
                    name="Toggle visibility",
                    icon=(f"{self._typed_state.name.is_visible} ? 'mdi-eye-outline' : 'mdi-eye-off-outline'",),
                    click=f"{self._typed_state.name.is_visible} = !{self._typed_state.name.is_visible}",
                )

            RangeSlider(
                classes="mx-3",
                typed_state=self._typed_state.get_sub_state(self._typed_state.name.threshold_slider),
            )
