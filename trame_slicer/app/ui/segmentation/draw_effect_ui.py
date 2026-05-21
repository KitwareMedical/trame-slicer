from dataclasses import dataclass

from trame.widgets import vuetify3 as vuetify
from trame_server.utils.typed_state import TypedState

from trame_slicer.segmentation.scissors_effect_parameters import BrushInteractionMode

from ..enum_to_title import enum_to_radio_buttons
from ..flex_container import FlexContainer


@dataclass
class DrawEffectState:
    brush_interaction_mode: BrushInteractionMode = BrushInteractionMode.CONTINUOUS


class DrawEffectUI(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, DrawEffectState)

        with (
            self,
            vuetify.VRow(style="margin-top: 2px; margin-bottom: 0px;"),
            vuetify.VRadioGroup(
                v_model=self._typed_state.name.brush_interaction_mode,
                label="Brush interaction mode",
                inline=True,
                hide_details=True,
            ),
        ):
            enum_to_radio_buttons(self._typed_state, BrushInteractionMode)
