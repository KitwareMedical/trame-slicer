from dataclasses import dataclass
from enum import Enum, auto

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VBtnToggle, VNumberInput, VSpacer
from undo_stack import Signal

from ..flex_container import FlexContainer


class IslandsSegmentationMode(Enum):
    KEEP_LARGEST_ISLAND = auto()
    REMOVE_SMALL_ISLANDS = auto()
    SPLIT_TO_SEGMENTS = auto()


@dataclass
class IslandsState:
    mode: IslandsSegmentationMode = IslandsSegmentationMode.KEEP_LARGEST_ISLAND
    minimum_size: int = 1000


class IslandsEffectUI(FlexContainer):
    apply_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, IslandsState)

        self.labels = {
            IslandsSegmentationMode.KEEP_LARGEST_ISLAND: "Keep largest",
            IslandsSegmentationMode.REMOVE_SMALL_ISLANDS: "Remove small",
            IslandsSegmentationMode.SPLIT_TO_SEGMENTS: "Split",
        }

        with self:
            with VBtnToggle(v_model=(self._typed_state.name.mode,), mandatory=True, style="align-self: center;"):
                for mode in IslandsSegmentationMode:
                    self._create_mode_button(mode)

            with FlexContainer(row=True, align="start", classes="mt-2"):
                VNumberInput(
                    v_if=(
                        f"{self._typed_state.name.mode} === {self._typed_state.encode(IslandsSegmentationMode.REMOVE_SMALL_ISLANDS)}",
                    ),
                    v_model=self._typed_state.name.minimum_size,
                    control_variant="stacked",
                    label="Minimum size",
                    min=(0,),
                    inset=True,
                    hide_details=True,
                    variant="solo-filled",
                    flat=True,
                    density="compact",
                )
                VSpacer()
                VBtn(text="Apply", prepend_icon="mdi-check", variant="tonal", click=self.apply_clicked)

    def _create_mode_button(self, mode: IslandsSegmentationMode):
        VBtn(text=self.labels[mode], value=(self._typed_state.encode(mode),), size="small")
