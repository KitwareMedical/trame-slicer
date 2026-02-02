from dataclasses import dataclass

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
    VBtn,
    VCard,
    VCardItem,
    VCardText,
    VDivider,
    VListItem,
    VSelect,
)

from trame_slicer.segmentation import SegmentationEditableAreaEnum

from ..text_components import Text
from .segment_list import SegmentListState


@dataclass
class SegmentOptionsState:
    editable_area: str = "EditAllowedEverywhere"
    is_extended: bool = False


class SegmentOptionsUI(VCard):
    def __init__(
        self,
        segment_options_typed_state: TypedState[SegmentOptionsState],
        segment_list_typed_state: TypedState[SegmentListState],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._typed_state = segment_options_typed_state
        self._segment_list_typed_state = segment_list_typed_state

        self._default_editable_areas_labels = {
            SegmentationEditableAreaEnum.EVERYWHERE: "Everywhere",
            SegmentationEditableAreaEnum.INSIDE_ALL_SEGMENTS: "Inside all segments",
            SegmentationEditableAreaEnum.INSIDE_ALL_VISIBLE_SEGMENTS: "Inside all visible segments",
            SegmentationEditableAreaEnum.OUTSIDE_ALL_SEGMENTS: "Outside all segments",
            SegmentationEditableAreaEnum.OUTSIDE_ALL_VISIBLE_SEGMENTS: "Outside all visible segments",
        }

        with self:
            with VCardItem():
                Text("Options", title=True)
                with Template(v_slot_append=True):
                    VBtn(
                        icon=(f"{self._typed_state.name.is_extended} ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                        variant="flat",
                        click=f"{self._typed_state.name.is_extended} = !{self._typed_state.name.is_extended};",
                        size="small",
                    )
            with VCardText(v_if=(self._typed_state.name.is_extended,), classes="align-center"):
                default_editable_area_options = [
                    {"text": label, "value": enum.value} for enum, label in self._default_editable_areas_labels.items()
                ]

                with (
                    VSelect(
                        v_model=self._typed_state.name.editable_area,
                        items=(
                            f"""
                            {default_editable_area_options}.concat(
                            {{type: 'separator'}},
                            {self._segment_list_typed_state.name.segments}.map(
                                (s, i) => ({{text: s.name, value: s.segment_id}}))
                            )
                            """,
                        ),
                        item_value="value",
                        item_title="text",
                        label="Editable Area",
                        hide_details=True,
                        density="compact",
                    ),
                    Template(v_slot_item="{ item, props }"),
                ):
                    VDivider(
                        v_if=("item.raw?.type === 'separator'",),
                        thickness=4,
                    )
                    VListItem(v_else=True, v_bind="props")
