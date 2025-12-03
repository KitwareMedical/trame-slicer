from dataclasses import dataclass, field
from typing import Any, Callable

from trame.widgets.vuetify3 import (
    VBtn,
    VCard,
    VCardActions,
    VCardItem,
    VCardText,
    VDivider,
    VSpacer,
    VTooltip,
)
from trame_client.widgets.core import AbstractElement, Template
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from examples.viewer_lib.ui.viewer_layout import ViewerLayoutState
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
from ..flex_container import FlexContainer
from .islands_effect_ui import IslandsEffectUI
from .paint_effect_ui import PaintEffectUI
from .segment_display_ui import SegmentDisplayState, SegmentDisplayUI
from .segment_edit_ui import SegmentEditUI
from .segment_list import SegmentList, SegmentListState
from .threshold_effect_ui import ThresholdEffectUI


@dataclass
class SegmentEditorState:
    segment_list: SegmentListState = field(default_factory=SegmentListState)
    segment_display: SegmentDisplayState = field(default_factory=SegmentDisplayState)
    can_undo: bool = False
    can_redo: bool = False
    active_effect_name: str = ""


class SegmentEditorUI(AbstractElement):
    toggle_segment_visibility_clicked = Signal(str)
    edit_segment_color_clicked = Signal(str)
    delete_segment_clicked = Signal(str)
    select_segment_clicked = Signal(str)
    add_segment_clicked = Signal()
    effect_button_clicked = Signal(type[SegmentationEffect])

    undo_clicked = Signal()
    redo_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(self.name, **kwargs)
        self._viewer_state = TypedState(self.state, ViewerLayoutState)
        self._typed_state = TypedState(self.state, SegmentEditorState)
        self._effect_ui: dict[type[SegmentationEffect], Any] = {}
        self.edit_ui = SegmentEditUI()

    @property
    def name(self):
        return "segment_editor"

    def _is_tool_active(self):
        return f"{self._viewer_state.name.active_tool} === '{self.name}'"

    def _is_tool_drawer_visible(self):
        return f"{self._is_tool_active()} && {self._viewer_state.name.is_drawer_visible}"

    def build_activator(self, click: Callable):
        ControlButton(
            icon="mdi-brush",
            name="{{ "
            + f"{self._is_tool_drawer_visible()} ? 'Close segmentation panel' : 'Open segmentation panel'"
            + " }}",
            click=lambda: click(self.name),
            active=(self._is_tool_active(),),
        )

    def build_drawer_ui(self):
        with FlexContainer(
            v_if=(self._is_tool_drawer_visible(),),
            fill_height=True,
        ):
            self.edit_ui._build_color_dialog()
            VBtn(
                v_if=(f"{self._typed_state.name.segment_list.segments}.length < 1",),
                classes="ma-4",
                click=self.add_segment_clicked,
                prepend_icon="mdi-plus",
                text="Add segment",
                variant="tonal",
                style="align-self: center;",
            )

            with FlexContainer(v_else=True, fill_height=True):
                with VCard(variant="flat", height="50%"):
                    with VCardText(style="height: calc(100% - 64px); overflow-y: auto;"):
                        self._create_segment_list()

                    with (
                        VCardActions(classes="justify-center", style="height: 64px;"),
                        VTooltip(text="Add Segment"),
                        Template(v_slot_activator="{ props }"),
                    ):
                        VBtn(
                            v_bind="props",
                            variant="tonal",
                            icon="mdi-plus",
                            click=self.add_segment_clicked,
                        )
                VDivider()
                with VCard(
                    v_if=(self._typed_state.name.segment_list.active_segment_id,), classes="flex-grow-1", variant="flat"
                ):
                    with VCardItem():
                        self._build_effect_buttons(row=True, justify="space-between")
                    VDivider(classes="mx-3")
                    with VCardText(classes="align-center"):
                        self._register_effect_ui(SegmentationEffectPaint, PaintEffectUI)
                        self._register_effect_ui(SegmentationEffectErase, PaintEffectUI)
                        self._register_effect_ui(SegmentationEffectThreshold, ThresholdEffectUI)
                        self._register_effect_ui(SegmentationEffectIslands, IslandsEffectUI)
                VSpacer(v_else=True)
                VDivider()
                SegmentDisplayUI(
                    typed_state=self.sub_state(self._typed_state.name.segment_display),
                    variant="flat",
                )

    def build_toolbar_ui(self):
        with FlexContainer(
            v_if=(self._is_tool_active(),),
            classes="flex-grow-1",
        ):
            VDivider(classes="my-2")
            VSpacer()
            self._build_effect_buttons(
                v_if=(f"!{self._viewer_state.name.is_drawer_visible}",),
                all=False,
            )
            VSpacer()
            VDivider(classes="my-2")
            self._build_undo_redo_buttons()

    def _build_effect_buttons(self, all: bool = True, **kwargs):
        with FlexContainer(**kwargs):
            self._create_effect_button(
                "No tool",
                "mdi-cursor-default",
                SegmentationEffectNoTool,
            )
            self._create_effect_button(
                "Paint",
                "mdi-brush",
                SegmentationEffectPaint,
            )
            self._create_effect_button(
                "Erase",
                "mdi-eraser",
                SegmentationEffectErase,
            )
            self._create_effect_button(
                "Scissors",
                "mdi-content-cut",
                SegmentationEffectScissors,
            )
            if all:
                self._create_effect_button(
                    "Threshold",
                    "mdi-auto-fix",
                    SegmentationEffectThreshold,
                )
                self._create_effect_button(
                    "Islands",
                    "mdi-scatter-plot",
                    SegmentationEffectIslands,
                )

    def _build_undo_redo_buttons(self, **kwargs):
        with FlexContainer(**kwargs):
            ControlButton(
                name="Undo",
                icon="mdi-undo",
                click=self.undo_clicked,
                disabled=(f"!{self._typed_state.name.can_undo}",),
            )
            ControlButton(
                name="Redo",
                icon="mdi-redo",
                click=self.redo_clicked,
                disabled=(f"!{self._typed_state.name.can_redo}",),
            )

    def _register_effect_ui(self, effect_cls: type[SegmentationEffect], effect_ui_type: type):
        self._effect_ui[effect_cls] = effect_ui_type(v_if=self.is_active_effect(effect_cls))

    def _create_segment_list(self):
        self._segment_list = SegmentList(
            typed_state=self.sub_state(self._typed_state.name.segment_list), edit_ui=self.edit_ui
        )
        self._segment_list.toggle_segment_visibility_clicked.connect(self.toggle_segment_visibility_clicked)
        self._segment_list.edit_segment_color_clicked.connect(self.edit_segment_color_clicked)
        self._segment_list.delete_segment_clicked.connect(self.delete_segment_clicked)
        self._segment_list.select_segment_clicked.connect(self.select_segment_clicked)

    def _create_effect_button(
        self,
        name: str,
        icon: str,
        effect_type: type[SegmentationEffect],
    ):
        ControlButton(
            v_if=(self._typed_state.name.segment_list.active_segment_id,),
            name=name,
            icon=icon,
            click=lambda: self.effect_button_clicked(effect_type),
            active=self.is_active_effect(effect_type),
        )

    def sub_state(self, sub_name):
        return self._typed_state.get_sub_state(sub_name)

    def is_active_effect(self, effect_type: type[SegmentationEffect]):
        name = effect_type.get_effect_name()
        return (f"{self._typed_state.name.active_effect_name} === '{name}'",)

    def get_effect_ui(self, effect_type: type[SegmentationEffect]):
        return self._effect_ui[effect_type]
