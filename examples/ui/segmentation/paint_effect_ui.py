from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VCheckbox, VContainer, VIcon, VRow

from trame_slicer.segmentation.paint_effect_parameters import BrushDiameterMode

from ..slider import Slider, SliderState


@dataclass
class PaintEffectState:
    brush_diameter_slider: SliderState = field(default_factory=SliderState)
    brush_diameter_mode: BrushDiameterMode = BrushDiameterMode.ScreenRelative
    use_sphere_brush: bool = True


class PaintEffectUI(VContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, PaintEffectState)
        self._typed_state.data.brush_diameter_slider.min_value = 1
        self._typed_state.data.brush_diameter_slider.max_value = 30
        self._typed_state.data.brush_diameter_slider.step = 1
        self._typed_state.data.brush_diameter_slider.value = 5

        with self:
            with VRow(classes="align-center"):
                VIcon("mdi-diameter-outline")
                Slider(self._typed_state.get_sub_state(self._typed_state.name.brush_diameter_slider))

            with VRow():
                VCheckbox(v_model=self._typed_state.name.use_sphere_brush, label="Sphere brush", density="compact")
