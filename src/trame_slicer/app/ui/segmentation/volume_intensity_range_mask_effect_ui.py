from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import Template, VIcon, VSwitch, VTooltip

from ..flex_container import FlexContainer
from ..slider import RangeSlider, RangeSliderState
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
            with FlexContainer(row=True, justify="space-between"):
                Text("Volume intensity range mask")
                with FlexContainer():
                    VTooltip(
                        activator="parent",
                        text=(f"{self._typed_state.name.is_enabled} ? 'Disable mask' : 'Enable mask'",),
                    )
                    VSwitch(
                        v_model=(self._typed_state.name.is_enabled,),
                        hide_details=True,
                        density="compact",
                    )

            with (
                RangeSlider(
                    typed_state=self._typed_state.get_sub_state(self._typed_state.name.threshold_slider),
                ),
                Template(v_slot_append=True),
            ):
                VIcon(
                    disabled=(f"!{self._typed_state.name.is_enabled}",),
                    name="Toggle mask visibility",
                    icon=(f"{self._typed_state.name.is_visible} ? 'mdi-eye-outline' : 'mdi-eye-off-outline'",),
                    click=f"{self._typed_state.name.is_visible} = !{self._typed_state.name.is_visible}",
                )
