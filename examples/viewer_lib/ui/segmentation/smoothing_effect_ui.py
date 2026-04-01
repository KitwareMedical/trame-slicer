from dataclasses import dataclass
from enum import Enum, auto

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
    VBtn,
    VNumberInput,
    VSelect,
    VSlider,
)
from undo_stack import Signal

from ..flex_container import FlexContainer
from .brush_parameters_ui import BrushParametersState, BrushParametersUI


class SmoothingEffectMode(Enum):
    MEDIAN = auto()
    OPENING = auto()
    CLOSING = auto()
    GAUSSIAN = auto()
    JOINT = auto()


@dataclass
class SmoothingState(BrushParametersState):
    mode: SmoothingEffectMode = SmoothingEffectMode.MEDIAN
    apply_to_all_visibile_segments: bool = False
    kernel_size: float = 3.0
    standard_deviation: float = 3.0
    smoothing_factor: float = 0.5


class SmoothingEffectUI(FlexContainer):
    apply_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, SmoothingState)
        self._typed_state.data.brush_diameter_slider.min_value = 1
        self._typed_state.data.brush_diameter_slider.max_value = 30
        self._typed_state.data.brush_diameter_slider.step = 1
        self._typed_state.data.brush_diameter_slider.value = 5

        with self:
            VSelect(
                v_model=self._typed_state.name.mode,
                items=(
                    "options",
                    self._typed_state.encode(
                        [{"text": st.name.title(), "value": self._typed_state.encode(st)} for st in SmoothingEffectMode]
                    ),
                ),
                item_title="text",
                item_value="value",
                hide_details=True,
                label="Smoothing method",
            )

            kernel_size_modes = [
                self._typed_state.encode(SmoothingEffectMode.MEDIAN),
                self._typed_state.encode(SmoothingEffectMode.CLOSING),
                self._typed_state.encode(SmoothingEffectMode.OPENING),
            ]
            with Template(v_if=(f"{kernel_size_modes}.includes({self._typed_state.name.mode})",)):
                VNumberInput(
                    v_model=self._typed_state.name.kernel_size,
                    classes="mt-2 mb-2",
                    hide_details=True,
                    control_variant="stacked",
                    precision=2,
                    min=0,
                    max=999,
                    step=(0.1,),
                    label="Kernel size (mm)",
                    density="comfortable",
                )
            with Template(
                v_if=(f"{self._typed_state.name.mode} == {self._typed_state.encode(SmoothingEffectMode.GAUSSIAN)}",)
            ):
                VNumberInput(
                    v_model=self._typed_state.name.standard_deviation,
                    classes="mt-2 mb-2",
                    hide_details=True,
                    control_variant="stacked",
                    precision=2,
                    min=0,
                    max=999,
                    step=(0.1,),
                    label="Standard deviation (mm)",
                    density="comfortable",
                )
            with Template(
                v_if=(f"{self._typed_state.name.mode} == {self._typed_state.encode(SmoothingEffectMode.JOINT)}",)
            ):
                VSlider(
                    v_model=self._typed_state.name.smoothing_factor,
                    classes="mt-2 mb-2",
                    hide_details=True,
                    min=0,
                    max=1,
                    step=0.01,
                    label="Smoothing factor",
                    density="comfortable",
                )
            VBtn("Apply", click=self.apply_clicked)
            BrushParametersUI(self._typed_state)
