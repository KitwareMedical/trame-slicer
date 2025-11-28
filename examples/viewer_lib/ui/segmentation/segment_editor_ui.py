from dataclasses import dataclass, field
from typing import Any

from trame_client.widgets.core import Template
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    VBtn,
    VContainer,
    VDivider,
    VRow,
    VTooltip,
)
from undo_stack import Signal

from trame_slicer.segmentation import (
    SegmentationEffect,
    SegmentationEffectErase,
    SegmentationEffectIslands,
    SegmentationEffectNoTool,
    SegmentationEffectPaint,
    SegmentationEffectScissors,
    SegmentationEffectThreshold,
)

from ..control_button import ControlButton
from .islands_effect_ui import IslandsEffectUI
from .paint_effect_ui import PaintEffectUI
from .segment_edit_dialog import SegmentEditDialog, SegmentEditDialogState
from .segment_list import SegmentList, SegmentListState
from .segment_opacity_ui import SegmentationOpacityUI, SegmentOpacityState
from .threshold_effect_ui import ThresholdEffectUI


@dataclass
class SegmentEditorState:
    segment_list: SegmentListState = field(default_factory=SegmentListState)
    segment_opacity: SegmentOpacityState = field(default_factory=SegmentOpacityState)
    can_undo: bool = False
    can_redo: bool = False
    show_3d: bool = False
    active_effect_name: str = ""


class SegmentEditorUI(VContainer):
    toggle_segment_visibility_clicked = Signal(str)
    edit_segment_clicked = Signal(str)
    delete_segment_clicked = Signal(str)
    select_segment_clicked = Signal(str)
    add_segment_clicked = Signal()
    effect_button_clicked = Signal(type[SegmentationEffect])

    undo_clicked = Signal()
    redo_clicked = Signal()
    show_3d_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(classes="pa-0 ma-0", **kwargs)
        self._typed_state = TypedState(self.state, SegmentEditorState)
        self._effect_ui: dict[type[SegmentationEffect], Any] = {}

        with self:
            self.edit_dialog = SegmentEditDialog(TypedState(self.state, SegmentEditDialogState))

            with VRow():
                ControlButton(
                    name="Undo",
                    icon="mdi-undo",
                    size=0,
                    click=self.undo_clicked,
                    disabled=(f"!{self._typed_state.name.can_undo}",),
                )
                ControlButton(
                    name="Redo",
                    icon="mdi-redo",
                    size=0,
                    style="margin-right: auto;",
                    click=self.redo_clicked,
                    disabled=(f"!{self._typed_state.name.can_redo}",),
                )

                ControlButton(
                    name="Toggle 3D",
                    icon="mdi-video-3d",
                    size=0,
                    click=self.show_3d_clicked,
                    active=(f"{self._typed_state.name.show_3d}",),
                )
                VDivider()

            with VRow(style="max-height: 300px; overflow-y: auto;"):
                self._create_segment_list()

            with VRow(classes="fill-width justify-center mb-4"):
                with VTooltip(text="Add Segment"), Template(v_slot_activator="{ props }"):
                    VBtn(
                        v_bind="props",
                        variant="tonal",
                        density="compact",
                        icon="mdi-plus",
                        click=self.add_segment_clicked,
                    )
                VDivider()

            with VRow():
                self._create_effect_button("No tool", "mdi-cursor-default", SegmentationEffectNoTool)
                self._create_effect_button("Paint", "mdi-brush", SegmentationEffectPaint)
                self._create_effect_button("Erase", "mdi-eraser", SegmentationEffectErase)
                self._create_effect_button("Scissors", "mdi-content-cut", SegmentationEffectScissors)
                self._create_effect_button("Threshold", "mdi-auto-fix", SegmentationEffectThreshold)
                self._create_effect_button("Islands", "mdi-scatter-plot", SegmentationEffectIslands)
                VDivider()

            with VRow():
                self._register_effect_ui(SegmentationEffectThreshold, ThresholdEffectUI)
                self._register_effect_ui(SegmentationEffectPaint, PaintEffectUI)
                self._register_effect_ui(SegmentationEffectErase, PaintEffectUI)
                self._register_effect_ui(SegmentationEffectIslands, IslandsEffectUI)

            with VRow():
                VBtn(
                    variant="text",
                    density="compact",
                    text="Opacity",
                    prepend_icon=(
                        f"{self._typed_state.name.segment_opacity.is_visible} ? 'mdi-menu-down' : 'mdi-menu-right' ",
                    ),
                    click=f"{self._typed_state.name.segment_opacity.is_visible} = !{self._typed_state.name.segment_opacity.is_visible}",
                    style="text-transform: none;",
                )

                self._opacity_ui = SegmentationOpacityUI(
                    typed_state=self.sub_state(self._typed_state.name.segment_opacity),
                    v_if=self._typed_state.name.segment_opacity.is_visible,
                )
                VDivider()

    def _register_effect_ui(self, effect_type: type[SegmentationEffect], effect_ui_type: type):
        self._effect_ui[effect_type] = effect_ui_type(v_if=self.button_active(effect_type))

    def _create_segment_list(self):
        self._segment_list = SegmentList(typed_state=self.sub_state(self._typed_state.name.segment_list))
        self._segment_list.toggle_segment_visibility_clicked.connect(self.toggle_segment_visibility_clicked)
        self._segment_list.edit_segment_clicked.connect(self.edit_segment_clicked)
        self._segment_list.delete_segment_clicked.connect(self.delete_segment_clicked)
        self._segment_list.select_segment_clicked.connect(self.select_segment_clicked)

    def _create_effect_button(self, name: str, icon: str, effect_type: type[SegmentationEffect]):
        return ControlButton(
            name=name,
            icon=icon,
            size=0,
            click=lambda: self.effect_button_clicked(effect_type),
            active=self.button_active(effect_type),
        )

    def sub_state(self, sub_name):
        return self._typed_state.get_sub_state(sub_name)

    def button_active(self, effect_cls: type[SegmentationEffect]):
        name = effect_cls.get_effect_name()
        return (f"{self._typed_state.name.active_effect_name} === '{name}'",)

    def get_effect_ui(self, effect_type: type[SegmentationEffect]):
        return self._effect_ui[effect_type]
