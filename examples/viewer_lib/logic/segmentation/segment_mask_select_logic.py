from __future__ import annotations

from dataclasses import dataclass

from trame_server.utils.typed_state import TypedState

from trame_slicer.core import SegmentationEditor
from trame_slicer.segmentation import SegmentationEditableAreaMode

from ...ui import DynamicSelectState, enum_to_title
from ..dynamic_select_logic import AbstractDynamicSelectLogic, IDynamicSelectItem


@dataclass
class SegmentMaskModeSelectItem(IDynamicSelectItem):
    editable_area: SegmentationEditableAreaMode = SegmentationEditableAreaMode.EVERYWHERE
    segment_id: str = ""
    segment_name: str = ""

    @property
    def title(self) -> str:
        return self.segment_name if self.segment_name else enum_to_title(self.editable_area)

    def matches(self, other: SegmentMaskModeSelectItem) -> bool:
        if self.editable_area != other.editable_area:
            return False

        if self.editable_area == SegmentationEditableAreaMode.INSIDE_SINGLE_SEGMENT:
            return self.segment_id == other.segment_id
        return True


class SegmentMaskSelectLogic(AbstractDynamicSelectLogic[SegmentMaskModeSelectItem]):
    def __init__(self, state: TypedState[DynamicSelectState], segmentation_editor: SegmentationEditor):
        super().__init__(state)
        self.segmentation_editor = segmentation_editor

    def _set_slicer_state(self, item: SegmentMaskModeSelectItem):
        self.segmentation_editor.set_mask_segment_id(item.segment_id)
        self.segmentation_editor.set_editable_area(item.editable_area)

    def _get_slicer_state(self) -> SegmentMaskModeSelectItem:
        return SegmentMaskModeSelectItem(
            self.segmentation_editor.get_editable_area(),
            self.segmentation_editor.get_mask_segment_id(),
        )

    def _get_current_items(self) -> list[SegmentMaskModeSelectItem]:
        mask_modes = [
            SegmentMaskModeSelectItem(editable_area=e)
            for e in SegmentationEditableAreaMode
            if e != SegmentationEditableAreaMode.INSIDE_SINGLE_SEGMENT
        ]

        mask_modes += [
            SegmentMaskModeSelectItem(
                editable_area=SegmentationEditableAreaMode.INSIDE_SINGLE_SEGMENT,
                segment_id=segment_id,
                segment_name=segment_name,
            )
            for segment_id, segment_name in zip(
                self.segmentation_editor.get_segment_ids(),
                self.segmentation_editor.get_segment_names(),
                strict=False,
            )
        ]

        return mask_modes
