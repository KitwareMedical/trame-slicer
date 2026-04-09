from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
)

from trame_slicer.segmentation import BrushDiameterMode
from trame_slicer.ui import Slider, SliderState

from ..control_button import ControlButton
from ..flex_container import FlexContainer
from ..text_components import Text


@dataclass
class BrushParametersState:
    brush_diameter_slider: SliderState = field(default_factory=SliderState)
    brush_diameter_mode: BrushDiameterMode = BrushDiameterMode.ScreenRelative
    use_sphere_brush: bool = True


class BrushParametersUI(FlexContainer):
    def __init__(self, typed_state: TypedState[BrushParametersState], **kwargs):
        super().__init__(**kwargs)

        with self:
            Text("Brush size", subtitle=True)
            with (
                Slider(typed_state=typed_state.get_sub_state(typed_state.name.brush_diameter_slider)),
                Template(v_slot_append=True),
            ):
                ControlButton(
                    icon="mdi-sphere",
                    name="Sphere brush",
                    click=f"{typed_state.name.use_sphere_brush} = ! {typed_state.name.use_sphere_brush}",
                    active=(typed_state.name.use_sphere_brush,),
                )
