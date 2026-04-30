from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
    VBtn,
    VCard,
    VCardItem,
    VCardText,
    VIcon,
    VRow,
    VSelect,
)

from trame_slicer.segmentation import SegmentationOverwriteMode

from ..color_dialog import ColorDialog
from ..dynamic_select import DynamicSelect, DynamicSelectState
from ..enum_to_title import enum_to_title
from ..text_components import Text


@dataclass
class SegmentEditAreaState:
    mask_select: DynamicSelectState = field(default_factory=DynamicSelectState)
    overwrite_mode: SegmentationOverwriteMode = SegmentationOverwriteMode.OVERWRITE_ALL
    is_extended: bool = False
    show_threshold_mask: bool = False
    threshold_mask_color: str = "#FF00004D"


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

                with VRow(style="margin-top: 15px; margin-right: 10px; margin-left: 10px; position: relative;"):
                    VIcon(
                        classes="mr-2",
                        icon="mdi-circle",
                        color=(self._typed_state.name.threshold_mask_color,),
                        click=(self.open_color_dialog,),
                    )
                    Text("Threshold Mask", title=True)
                    VIcon(
                        icon=(
                            f"{self._typed_state.name.show_threshold_mask} ? 'mdi-eye-outline' : 'mdi-eye-off-outline'",
                        ),
                        click=f"{self._typed_state.name.show_threshold_mask} = !{self._typed_state.name.show_threshold_mask}",
                        style="position: absolute; right:0;",
                    )

                self.color_dialog = ColorDialog(self._typed_state.name.threshold_mask_color, mode="rgba", width="auto")
                self.color_dialog.apply_clicked.connect(self._color_changed)
                self.color_dialog.cancel_clicked.connect(self._cancel_clicked)

    def open_color_dialog(self):
        self.color_dialog.set_color(self._typed_state.data.threshold_mask_color)
        self.color_dialog.open()

    def _color_changed(self):
        self.color_dialog.close()
        self._typed_state.data.threshold_mask_color = self.color_dialog.get_color()

    def _cancel_clicked(self):
        self.color_dialog.close()
        self.color_dialog.set_color(self._typed_state.data.threshold_mask_color)
