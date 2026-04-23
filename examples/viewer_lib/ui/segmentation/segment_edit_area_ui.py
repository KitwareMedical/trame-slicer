from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
    VBtn,
    VCard,
    VCardItem,
    VCardText,
    VSelect,
)

from trame_slicer.segmentation import SegmentationOverwriteMode

from ..dynamic_select import DynamicSelect, DynamicSelectState
from ..enum_to_title import enum_to_title
from ..text_components import Text


@dataclass
class SegmentEditAreaState:
    mask_select: DynamicSelectState = field(default_factory=DynamicSelectState)
    overwrite_mode: SegmentationOverwriteMode = SegmentationOverwriteMode.OVERWRITE_ALL
    is_extended: bool = False


class SegmentEditAreaUI(VCard):
    def __init__(self, segment_edit_area_typed_state: TypedState[SegmentEditAreaState], **kwargs):
        super().__init__(**kwargs)
        self._typed_state = segment_edit_area_typed_state

        with self:
            with VCardItem(
                click=f"{self._typed_state.name.is_extended} = !{self._typed_state.name.is_extended};",
            ):
                Text("Masking options", title=True)
                with Template(v_slot_append=True):
                    VBtn(
                        icon=(f"{self._typed_state.name.is_extended} ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                        variant="flat",
                        click_stop=f"{self._typed_state.name.is_extended} = !{self._typed_state.name.is_extended};",
                        size="small",
                    )

            with VCardText(
                v_if=(self._typed_state.name.is_extended,),
                classes="align-center",
            ):
                DynamicSelect(
                    label="Editable Area",
                    state=self._typed_state.get_sub_state(self._typed_state.name.mask_select),
                )
                VSelect(
                    label="Overwrite mode",
                    v_model=self._typed_state.name.overwrite_mode,
                    items=(
                        [
                            {"title": enum_to_title(e), "value": self._typed_state.encode(e)}
                            for e in SegmentationOverwriteMode
                        ],
                    ),
                    item_value="value",
                    item_title="title",
                    hide_details=True,
                    density="compact",
                    style="margin-top: 5px;",
                )
