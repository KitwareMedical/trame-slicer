from slicer import vtkMRMLVolumeNode
from trame_server import Server
from undo_stack import UndoStack

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import (
    SegmentationDisplay,
    SegmentationEditableArea,
    SegmentationEffect,
    SegmentationEffectThreshold,
    SegmentMaskingParameters,
)

from ...ui import (
    SegmentDisplayState,
    SegmentEditAreaState,
    SegmentEditorState,
    SegmentEditorUI,
    SegmentState,
)
from .base_segmentation_logic import BaseEffectLogic, BaseSegmentationLogic
from .islands_effect_logic import IslandsEffectLogic
from .paint_erase_effect_logic import EraseEffectLogic, PaintEffectLogic
from .segment_edit_logic import SegmentEditLogic
from .threshold_effect_logic import ThresholdEffectLogic


class SegmentEditorLogic(BaseSegmentationLogic[SegmentEditorState]):
    def __init__(self, server: Server, slicer_app: SlicerApp):
        super().__init__(server=server, slicer_app=slicer_app, state_type=SegmentEditorState)

        effect_logic = [
            IslandsEffectLogic,
            ThresholdEffectLogic,
            PaintEffectLogic,
            EraseEffectLogic,
        ]
        self._effect_logic: list[BaseEffectLogic] = [logic(server, slicer_app) for logic in effect_logic]
        self._edit_segment_logic = SegmentEditLogic(server, slicer_app)

        self._undo_stack = UndoStack(undo_limit=5)
        self.segmentation_editor.set_undo_stack(self._undo_stack)

        self._connect_segmentation_editor_to_state()
        self._connect_undo_stack_to_state()
        self.bind_changes(
            {
                self.name.segment_display: self._on_segment_display_changed,
                self.name.segment_list.active_segment_id: self._on_active_segment_changed,
                self.name.segment_edit_area: self._on_segment_edit_area_changed,
            }
        )

    def _connect_segmentation_editor_to_state(self):
        for sig in self.segmentation_editor.signals():
            sig.connect(self._on_segment_editor_changed)

    def _connect_undo_stack_to_state(self):
        for sig in self._undo_stack.signals():
            sig.connect(self._on_undo_changed)

    def set_ui(self, ui: SegmentEditorUI):
        ui.toggle_segment_visibility_clicked.connect(self._on_toggle_segment_visibility_clicked)
        ui.edit_segment_color_clicked.connect(self._on_edit_segment_color_clicked)
        ui.delete_segment_clicked.connect(self._on_delete_segment_clicked)
        ui.select_segment_clicked.connect(self._on_select_segment_clicked)
        ui.add_segment_clicked.connect(self._on_add_segment_clicked)
        ui.effect_button_clicked.connect(self._on_effect_button_clicked)
        ui.undo_clicked.connect(self._on_undo_clicked)
        ui.redo_clicked.connect(self._on_redo_clicked)

        for logic in self._effect_logic:
            logic.set_ui(ui)

        self._edit_segment_logic.set_ui(ui.edit_ui)

    def _on_toggle_segment_visibility_clicked(self, segment_id: str):
        self.segmentation_editor.set_segment_visibility(
            segment_id, not self.segmentation_editor.get_segment_visibility(segment_id)
        )
        self._update_segment_list()

    def _on_edit_segment_color_clicked(self, *_args):
        self._edit_segment_logic.show_color_dialog()

    def _on_active_segment_changed(self, segment_id: str):
        if not segment_id and len(self.data.segment_list.segments) > 0:
            self.data.segment_list.active_segment_id = self.data.segment_list.segments[0].segment_id
        else:
            self._edit_segment_logic.set_active_segment_id(segment_id)

    def _on_segment_edit_area_changed(self, options_state: SegmentEditAreaState):
        if self.segmentation_editor.active_segmentation is None:
            return

        editable_area = options_state.editable_area
        overwrite_mode = options_state.overwrite_mode
        # SegmentEditAreaState holds a string that can represent a mask mode or segment ID
        # whereas SegmentationEditableArea needs a proper mask mode or segment ID
        if editable_area in self.segmentation_editor.get_segment_ids():
            parameters = SegmentMaskingParameters(
                overwrite_mode=overwrite_mode,
                segment_id=editable_area,
            )
        else:
            parameters = SegmentMaskingParameters(
                editable_area=SegmentationEditableArea(
                    self.segmentation_editor.active_segmentation.segmentation_node.ConvertMaskModeFromString(
                        editable_area
                    )
                ),
                overwrite_mode=overwrite_mode,
            )
        self.segmentation_editor.set_masking_parameters(parameters)

    def _on_delete_segment_clicked(self, segment_id: str):
        self.segmentation_editor.remove_segment(segment_id)

    def _on_select_segment_clicked(self, segment_id: str):
        self.segmentation_editor.set_active_segment_id(segment_id)

    def _on_add_segment_clicked(self):
        self.segmentation_editor.add_empty_segment()

    def _on_effect_button_clicked(self, effect_type: type[SegmentationEffect]):
        self.segmentation_editor.set_active_effect_type(effect_type)

    def _on_undo_clicked(self):
        self._undo_stack.undo()

    def _on_redo_clicked(self):
        self._undo_stack.redo()

    def _on_apply_threshold_clicked(self):
        effect = self.segmentation_editor.active_effect
        if not isinstance(effect, SegmentationEffectThreshold):
            return
        effect.apply()
        self.segmentation_editor.deactivate_effect()

    def _on_segment_editor_changed(self, *_):
        self.data.segment_list.active_segment_id = self.segmentation_editor.get_active_segment_id()
        self.data.segment_display.show_3d = self.segmentation_editor.is_surface_representation_enabled()
        self.data.active_effect_name = self.segmentation_editor.get_active_effect_name()

        segment_modification_parameters = self.segmentation_editor.get_masking_parameters()
        if segment_modification_parameters is not None:
            editable_area = segment_modification_parameters.editable_area
            if editable_area == SegmentationEditableArea.INSIDE_SINGLE_SEGMENT:
                editable_area_string = segment_modification_parameters.segment_id
            else:
                editable_area_string = (
                    self.segmentation_editor.active_segmentation.segmentation_node.ConvertMaskModeToString(
                        editable_area.value
                    )
                )
            self.data.segment_edit_area.editable_area = editable_area_string

            self.data.segment_edit_area.overwrite_mode = segment_modification_parameters.overwrite_mode

        self._update_segment_list()

    def _on_undo_changed(self, *_):
        self.data.can_undo = self._undo_stack.can_undo()
        self.data.can_redo = self._undo_stack.can_redo()
        self._update_segment_list()
        self.data.segment_list.active_segment_id = self.segmentation_editor.get_active_segment_id()

    def _update_segment_list(self):
        self.data.segment_list.segments = [
            SegmentState(
                name=segment_properties.name,
                color=segment_properties.color_hex,
                segment_id=segment_id,
                is_visible=self.segmentation_editor.get_segment_visibility(segment_id),
            )
            for segment_id, segment_properties in self.segmentation_editor.get_all_segment_properties().items()
        ]

    @property
    def _segmentation_display(self) -> SegmentationDisplay | None:
        return self.segmentation_editor.active_segmentation_display

    def _on_segment_display_changed(self, display_state: SegmentDisplayState) -> None:
        if not self._segmentation_display:
            return

        self._segmentation_display.set_opacity_2d(display_state.opacity_2d.value)
        self._segmentation_display.set_opacity_3d(display_state.opacity_3d.value)
        self._segmentation_display.set_opacity_mode(display_state.opacity_mode)
        self.segmentation_editor.set_surface_representation_enabled(display_state.show_3d)

    def on_volume_changed(self, volume_node: vtkMRMLVolumeNode) -> None:
        segmentation_nodes = list(self.scene.GetNodesByClass("vtkMRMLSegmentationNode"))
        if segmentation_nodes:
            segmentation_node = segmentation_nodes[0]
        else:
            segmentation_node = self.segmentation_editor.create_empty_segmentation_node()

        self.segmentation_editor.deactivate_effect()
        self.segmentation_editor.set_active_segmentation(
            segmentation_node,
            volume_node,
        )
        self._on_segment_display_changed(self.data.segment_display)
