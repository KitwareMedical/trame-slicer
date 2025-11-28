from trame_server import Server
from undo_stack import UndoStack

from trame_slicer.core import SlicerApp
from trame_slicer.segmentation import (
    SegmentationDisplay,
    SegmentationEffect,
    SegmentationEffectThreshold,
)

from ...ui import (
    SegmentEditorState,
    SegmentEditorUI,
    SegmentOpacityState,
    SegmentState,
    StateId,
    get_current_volume_node,
)
from .base_segmentation_logic import BaseEffectLogic, BaseSegmentationLogic
from .islands_effect_logic import IslandsEffectLogic
from .paint_erase_effect_logic import EraseEffectLogic, PaintEffectLogic
from .segment_edit_dialog_logic import SegmentEditDialogLogic
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
        self._edit_dialog_logic = SegmentEditDialogLogic(server, slicer_app)

        self._undo_stack = UndoStack(undo_limit=5)
        self.segmentation_editor.set_undo_stack(self._undo_stack)

        self._connect_segmentation_editor_to_state()
        self._connect_undo_stack_to_state()
        self.bind_changes(
            {self.name.segment_opacity: self._on_opacity_changed, self.name.show_3d: self._on_show_3d_changed}
        )
        self.state.change(StateId.current_volume_node_id)(self._on_volume_changed)

    def _connect_segmentation_editor_to_state(self):
        for sig in self.segmentation_editor.signals():
            sig.connect(self._on_segment_editor_changed)

    def _connect_undo_stack_to_state(self):
        for sig in self._undo_stack.signals():
            sig.connect(self._on_undo_changed)

    def set_ui(self, ui: SegmentEditorUI):
        ui.toggle_segment_visibility_clicked.connect(self._on_toggle_segment_visibility_clicked)
        ui.edit_segment_clicked.connect(self._on_edit_segment_clicked)
        ui.delete_segment_clicked.connect(self._on_delete_segment_clicked)
        ui.select_segment_clicked.connect(self._on_select_segment_clicked)
        ui.add_segment_clicked.connect(self._on_add_segment_clicked)
        ui.effect_button_clicked.connect(self._on_effect_button_clicked)
        ui.undo_clicked.connect(self._on_undo_clicked)
        ui.redo_clicked.connect(self._on_redo_clicked)
        ui.show_3d_clicked.connect(self._on_show_3d_clicked)

        for logic in self._effect_logic:
            logic.set_ui(ui)

        self._edit_dialog_logic.set_ui(ui)

    def _on_toggle_segment_visibility_clicked(self, segment_id: str):
        self.segmentation_editor.set_segment_visibility(
            segment_id, not self.segmentation_editor.get_segment_visibility(segment_id)
        )
        self._update_segment_list()

    def _on_edit_segment_clicked(self, segment_id: str):
        self._edit_dialog_logic.show_dialog(segment_id)

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
        self.data.show_3d = self.segmentation_editor.is_surface_representation_enabled()
        self.data.active_effect_name = self.segmentation_editor.get_active_effect_name()
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

    def _on_opacity_changed(self, opacity_state: SegmentOpacityState) -> None:
        if not self._segmentation_display:
            return

        self._segmentation_display.set_opacity_2d(opacity_state.opacity_2d)
        self._segmentation_display.set_opacity_3d(opacity_state.opacity_3d)
        self._segmentation_display.set_opacity_mode(opacity_state.opacity_mode)

    def _on_volume_changed(self, **_kwargs) -> None:
        segmentation_nodes = list(self.scene.GetNodesByClass("vtkMRMLSegmentationNode"))
        if segmentation_nodes:
            segmentation_node = segmentation_nodes[0]
        else:
            segmentation_node = self.segmentation_editor.create_empty_segmentation_node()

        self.segmentation_editor.deactivate_effect()
        self.segmentation_editor.set_active_segmentation(
            segmentation_node,
            get_current_volume_node(self._server, self._slicer_app),
        )
        self._on_opacity_changed(self.data.segment_opacity)

        if self.segmentation_editor.active_segmentation.n_segments == 0:
            self._on_add_segment_clicked()

    def _on_show_3d_clicked(self) -> None:
        self.data.show_3d = not self.data.show_3d

    def _on_show_3d_changed(self, show_3d: bool) -> None:
        self.segmentation_editor.set_surface_representation_enabled(show_3d)
