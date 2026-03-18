from dataclasses import dataclass

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VBtnToggle, VNumberInput, VSpacer
from undo_stack import Signal

from trame_slicer.segmentation import SegmentationIslandsMode

from ..flex_container import FlexContainer


@dataclass
class IslandsState:
    mode: SegmentationIslandsMode = SegmentationIslandsMode.KEEP_LARGEST_ISLAND
    minimum_size: int = 1000


class IslandsEffectUI(FlexContainer):
    apply_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, IslandsState)

        self.labels = {
            SegmentationIslandsMode.KEEP_LARGEST_ISLAND: "Keep largest",
            SegmentationIslandsMode.REMOVE_SMALL_ISLANDS: "Remove small",
            SegmentationIslandsMode.SPLIT_TO_SEGMENTS: "Split",
            SegmentationIslandsMode.KEEP_SELECTED: "Keep selected",
            SegmentationIslandsMode.REMOVE_SELECTED: "Remove selected",
            SegmentationIslandsMode.ADD_SELECTED: "Add selected",
        }

        with self:
            with VBtnToggle(
                v_model=(self._typed_state.name.mode,),
                mandatory=True,
                style="align-self: center; height: fit-content; display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;",
            ):
                for mode in SegmentationIslandsMode:
                    self._create_mode_button(mode)

            with FlexContainer(row=True, align="start", classes="mt-2"):
                VNumberInput(
                    v_if=(
                        f"{self._typed_state.name.mode} === {self._typed_state.encode(SegmentationIslandsMode.REMOVE_SMALL_ISLANDS)}",
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
                VBtn(
                    text="Apply",
                    prepend_icon="mdi-check",
                    variant="tonal",
                    click=self.apply_clicked,
                    disabled=(
                        f"{self._typed_state.encode(SegmentationIslandsMode.get_interactive_modes())}.includes({self._typed_state.name.mode})",
                    ),
                    style="margin-top: 16px !important;",
                )

    def _create_mode_button(self, mode: SegmentationIslandsMode):
        VBtn(text=self.labels[mode], value=(self._typed_state.encode(mode),), size="small", style="min-height: 30px;")
