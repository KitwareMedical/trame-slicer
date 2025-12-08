from dataclasses import dataclass, field

from trame.widgets.vuetify3 import Template
from trame_server.utils.typed_state import TypedState

from trame_slicer.segmentation.paint_effect_parameters import BrushDiameterMode

from ..control_button import ControlButton
from ..flex_container import FlexContainer
from ..slider import Slider, SliderState
from ..text_components import Text


@dataclass
class PaintEffectState:
    brush_diameter_slider: SliderState = field(default_factory=SliderState)
    brush_diameter_mode: BrushDiameterMode = BrushDiameterMode.ScreenRelative
    use_sphere_brush: bool = True


class PaintEffectUI(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, PaintEffectState)
        self._typed_state.data.brush_diameter_slider.min_value = 1
        self._typed_state.data.brush_diameter_slider.max_value = 30
        self._typed_state.data.brush_diameter_slider.step = 1
        self._typed_state.data.brush_diameter_slider.value = 5

        with self:
            Text("Brush size", subtitle=True)
            with (
                Slider(typed_state=self._typed_state.get_sub_state(self._typed_state.name.brush_diameter_slider)),
                Template(v_slot_append=True),
            ):
                ControlButton(
                    icon="mdi-sphere",
                    name="Sphere brush",
                    click=f"{self._typed_state.name.use_sphere_brush} = ! {self._typed_state.name.use_sphere_brush}",
                    active=(self._typed_state.name.use_sphere_brush,),
                )
