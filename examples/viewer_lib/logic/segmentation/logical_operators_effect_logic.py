from trame_server import Server

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import SegmentationEffectLogicalOperators

from ...ui import (
    LogicalOperatorsEffectUI,
    LogicalOperatorsSegmentationMode,
    LogicalOperatorsState,
    SegmentEditorUI,
    SegmentState,
)
from .base_segmentation_logic import BaseEffectLogic


class LogicalOperatorsEffectLogic(BaseEffectLogic[LogicalOperatorsState, SegmentationEffectLogicalOperators]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server, slicer_app, LogicalOperatorsState, SegmentationEffectLogicalOperators)
        self.segmentation_editor.active_segment_id_changed.connect(self._update_available_segments)

    def set_ui(self, ui: SegmentEditorUI):
        self.set_effect_ui(ui.get_effect_ui(SegmentationEffectLogicalOperators))

    def set_effect_ui(self, logical_operators_ui: LogicalOperatorsEffectUI):
        logical_operators_ui.apply_clicked.connect(self._on_apply_clicked)

    def _update_available_segments(self, *_args, **_kwargs):
        self.data.available_segments = [
            SegmentState(
                name=segment_properties.name,
                color=segment_properties.color_hex,
                segment_id=segment_id,
                is_visible=self.segmentation_editor.get_segment_visibility(segment_id),
            )
            for segment_id, segment_properties in self.segmentation_editor.get_all_segment_properties().items()
        ]
        if self.data.reference_segment_id not in [segment.segment_id for segment in self.data.available_segments]:
            self.data.reference_segment_id = None

    def _on_apply_clicked(self):
        if not self.is_active():
            return

        reference_segment_id = self.data.reference_segment_id

        match self.data.logical_operator:
            case LogicalOperatorsSegmentationMode.ADD:
                if reference_segment_id is None:
                    return
                self.effect.add(reference_segment_id)
            case LogicalOperatorsSegmentationMode.COPY:
                if reference_segment_id is None:
                    return
                self.effect.copy(reference_segment_id)
            case LogicalOperatorsSegmentationMode.SUBTRACT:
                if reference_segment_id is None:
                    return
                self.effect.subtract(reference_segment_id)
            case LogicalOperatorsSegmentationMode.INTERSECT:
                if reference_segment_id is None:
                    return
                self.effect.intersect(reference_segment_id)
            case LogicalOperatorsSegmentationMode.INVERT:
                self.effect.invert()
            case LogicalOperatorsSegmentationMode.CLEAR:
                self.effect.clear()
            case LogicalOperatorsSegmentationMode.FILL:
                self.effect.fill()
            case _:
                err = f"Invalid logical operator {self.data.logical_operator}"
                raise ValueError(err)
