from dataclasses import dataclass

from trame.widgets import vuetify3 as vuetify
from trame_server.utils.typed_state import TypedState

from trame_slicer.segmentation.scissors_effect_parameters import (
    BrushInteractionMode,
    ScissorsEffectFillMode,
    ScissorsEffectRangeMode,
)

from ..enum_to_title import enum_to_radio_buttons
from ..flex_container import FlexContainer


@dataclass
class ScissorsEffectState:
    brush_interaction_mode: BrushInteractionMode = BrushInteractionMode.CONTINUOUS
    fill_mode: ScissorsEffectFillMode = ScissorsEffectFillMode.ERASE_INSIDE
    range_mode: ScissorsEffectRangeMode = ScissorsEffectRangeMode.UNLIMITED
    symmetric_distance: float = 0


class ScissorsEffectUI(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, ScissorsEffectState)

        with self:
            with (
                vuetify.VRow(style="margin-top: 20px;"),
                vuetify.VRadioGroup(
                    v_model=self._typed_state.name.brush_interaction_mode,
                    label="Brush interaction mode",
                    inline=True,
                    hide_details=True,
                ),
            ):
                enum_to_radio_buttons(self._typed_state, BrushInteractionMode)
            with vuetify.VRow(style="margin-top: 20px;"):
                with (
                    vuetify.VCol(style="padding: 0;"),
                    vuetify.VRadioGroup(v_model=self._typed_state.name.fill_mode, label="Operation", hide_details=True),
                ):
                    enum_to_radio_buttons(self._typed_state, ScissorsEffectFillMode)

                with (
                    vuetify.VCol(style="padding: 0;"),
                    vuetify.VRadioGroup(v_model=self._typed_state.name.range_mode, label="Cut mode", hide_details=True),
                ):
                    enum_to_radio_buttons(self._typed_state, ScissorsEffectRangeMode)
            with vuetify.VRow(style="margin-top: 20px; margin-left: 2px; margin-right: 2px;"):
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
