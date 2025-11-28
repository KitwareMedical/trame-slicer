from dataclasses import dataclass
from enum import Enum, auto

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VContainer, VNumberInput, VSelect
from undo_stack import Signal


class IslandsSegmentationMode(Enum):
    KEEP_LARGEST_ISLAND = auto()
    REMOVE_SMALL_ISLANDS = auto()
    SPLIT_TO_SEGMENTS = auto()


@dataclass
class IslandsState:
    mode: IslandsSegmentationMode = IslandsSegmentationMode.KEEP_LARGEST_ISLAND
    minimum_size: int = 1000


class IslandsEffectUI(VContainer):
    apply_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(classes="fill-width", **kwargs)
        self._typed_state = TypedState(self.state, IslandsState)

        self.labels = {
            IslandsSegmentationMode.KEEP_LARGEST_ISLAND: "Keep largest island",
            IslandsSegmentationMode.REMOVE_SMALL_ISLANDS: "Remove small islands",
            IslandsSegmentationMode.SPLIT_TO_SEGMENTS: "Split to segments",
        }

        with self:
            VSelect(
                v_model=self._typed_state.name.mode,
                items=(
                    [
                        {"title": self.labels[mode], "value": self._typed_state.encode(mode)}
                        for mode in IslandsSegmentationMode
                    ],
                ),
                hide_details=True,
                density="compact",
                label="Mode",
            )
            VNumberInput(
                v_model=self._typed_state.name.minimum_size,
                label="Minimum size",
                disabled=(
                    f"{self._typed_state.name.mode} !== {self._typed_state.encode(IslandsSegmentationMode.REMOVE_SMALL_ISLANDS)}",
                ),
                min=(0,),
                hide_details=True,
                density="compact",
                classes="mt-5",
            )
            VBtn("Apply", prepend_icon="mdi-check-outline", block=True, click=self.apply_clicked, classes="mt-5")
