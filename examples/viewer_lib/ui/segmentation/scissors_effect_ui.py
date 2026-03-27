from dataclasses import dataclass

from trame.widgets import vuetify3 as vuetify
from trame_server.utils.typed_state import TypedState

from trame_slicer.segmentation.scissors_effect_parameters import (
    ScissorsEffectFillMode,
    ScissorsEffectRangeMode,
)

from ..flex_container import FlexContainer


@dataclass
class ScissorsEffectState:
    fill_mode: ScissorsEffectFillMode = ScissorsEffectFillMode.ERASE_INSIDE
    range_mode: ScissorsEffectRangeMode = ScissorsEffectRangeMode.UNLIMITED
    symmetric_distance: float = 0


class ScissorsEffectUI(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, ScissorsEffectState)

        fill_mode_dict = {
            ScissorsEffectFillMode.ERASE_INSIDE: "Erase Inside",
            ScissorsEffectFillMode.ERASE_OUTSIDE: "Erase Outside",
            ScissorsEffectFillMode.FILL_INSIDE: "Fill Inside",
            ScissorsEffectFillMode.FILL_OUTSIDE: "Fill Outside",
        }

        range_mode_dict = {
            ScissorsEffectRangeMode.UNLIMITED: "Unlimited",
            ScissorsEffectRangeMode.POSITIVE: "Positive",
            ScissorsEffectRangeMode.NEGATIVE: "Negative",
            ScissorsEffectRangeMode.SYMMETRIC: "Symmetric",
        }

        with self:
            with vuetify.VRow():
                with (
                    vuetify.VCol(),
                    vuetify.VRadioGroup(v_model=self._typed_state.name.fill_mode, label="Operation"),
                ):
                    temp = self._typed_state.encode(
                        [
                            {
                                "text": text,
                                "value": value,
                            }
                            for value, text in fill_mode_dict.items()
                        ]
                    )
                    vuetify.VRadio(
                        v_for=f"operation in {temp}",
                        label=("operation.text",),
                        value=("operation.value",),
                    )

                with (
                    vuetify.VCol(),
                    vuetify.VRadioGroup(v_model=self._typed_state.name.range_mode, label="Cut mode"),
                ):
                    temp = self._typed_state.encode(
                        [
                            {
                                "text": text,
                                "value": value,
                            }
                            for value, text in range_mode_dict.items()
                        ]
                    )
                    vuetify.VRadio(
                        v_for=f"operation in {temp}",
                        label=("operation.text",),
                        value=("operation.value",),
                    )
            with vuetify.VRow():
                vuetify.VNumberInput(
                    v_model=self._typed_state.name.symmetric_distance,
                    label="Distance (mm)",
                    disabled=(
                        f"{self._typed_state.name.range_mode} !== {self._typed_state.encode(ScissorsEffectRangeMode.SYMMETRIC)}",
                    ),
                    min=0,
                    max=9999,
                    step=(0.0001,),
                    precision=4,
                    density="comfortable",
                    control_variant="stacked",
                    hide_details=True,
                )
