from dataclasses import dataclass, field
from enum import Enum, auto

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VSelect
from undo_stack import Signal

from ..flex_container import FlexContainer
from .segment_state import SegmentState


class LogicalOperatorsSegmentationMode(Enum):
    COPY = auto()
    ADD = auto()
    SUBTRACT = auto()
    INTERSECT = auto()
    INVERT = auto()
    CLEAR = auto()
    FILL = auto()


@dataclass
class LogicalOperatorsState:
    logical_operator: LogicalOperatorsSegmentationMode = LogicalOperatorsSegmentationMode.COPY
    reference_segment_id: str | None = None
    available_segments: list[SegmentState] = field(default_factory=list)


class LogicalOperatorsEffectUI(FlexContainer):
    apply_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typed_state = TypedState(self.state, LogicalOperatorsState)

        modes_with_reference = [
            LogicalOperatorsSegmentationMode.COPY,
            LogicalOperatorsSegmentationMode.ADD,
            LogicalOperatorsSegmentationMode.SUBTRACT,
            LogicalOperatorsSegmentationMode.INTERSECT,
        ]

        with self:
            VSelect(
                v_model=self._typed_state.name.logical_operator,
                label="Logical Operator",
                density="comfortable",
                hide_details=True,
                item_title="title",
                item_value="value",
                items=(
                    [
                        {"title": mode.name.capitalize(), "value": self._typed_state.encode(mode)}
                        for mode in LogicalOperatorsSegmentationMode
                    ],
                ),
            )
            is_mode_with_reference_state_str = f"{[self._typed_state.encode(mode) for mode in modes_with_reference]}.includes({self._typed_state.name.logical_operator})"
            VSelect(
                v_model=self._typed_state.name.reference_segment_id,
                label="Reference segment",
                density="comfortable",
                hide_details=True,
                item_title="title",
                item_value="value",
                items=(
                    f"{self._typed_state.name.available_segments}.map((segment) => ({{ 'title': segment.name, 'value': segment.segment_id }}))",
                ),
                v_if=(is_mode_with_reference_state_str,),
            )
            available_segment_ids = f"{self._typed_state.name.available_segments}.map((segment) => segment.segment_id)"
            VBtn(
                "Apply",
                click=self.apply_clicked,
                disabled=(
                    f"{is_mode_with_reference_state_str} && ({self._typed_state.name.reference_segment_id} === null || !{available_segment_ids}.includes({self._typed_state.name.reference_segment_id}))",
                ),
            )
