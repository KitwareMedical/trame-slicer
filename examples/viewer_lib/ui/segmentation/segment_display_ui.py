from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
    VBtn,
    VCard,
    VCardItem,
    VCardText,
)

from trame_slicer.segmentation import SegmentationOpacityEnum

from ..control_button import ControlButton
from ..flex_container import FlexContainer
from ..slider import Slider, SliderState
from ..text_components import Text


@dataclass
class SegmentDisplayState:
    opacity_mode: SegmentationOpacityEnum = SegmentationOpacityEnum.BOTH
    opacity_2d: SliderState = field(default_factory=SliderState)
    opacity_3d: SliderState = field(default_factory=SliderState)
    show_3d: bool = False
    is_extended: bool = False


class SegmentDisplayUI(VCard):
    def __init__(self, typed_state: TypedState[SegmentDisplayState], **kwargs):
        super().__init__(**kwargs)

        self._typed_state = typed_state
        self._typed_state.data.opacity_2d.step = 0.01
        self._typed_state.data.opacity_3d.step = 0.01
        self._typed_state.data.opacity_3d.value = 1

        with self:
            with VCardItem():
                Text("Rendering", title=True)
                with Template(v_slot_append=True):
                    VBtn(
                        icon=(f"{self._typed_state.name.is_extended} ? 'mdi-chevron-up' : 'mdi-chevron-down'",),
                        variant="flat",
                        click=f"{self._typed_state.name.is_extended} = !{self._typed_state.name.is_extended};",
                        size="small",
                    )
            with VCardText(v_if=(self._typed_state.name.is_extended,), classes="align-center"):
                Text("Display", subtitle=True)
                with FlexContainer(
                    justify="space-between",
                    row=True,
                ):
                    VBtn(
                        active=(
                            "["
                            f"{self._typed_state.encode(SegmentationOpacityEnum.FILL)}, {self._typed_state.encode(SegmentationOpacityEnum.BOTH)}"
                            f"].includes({self._typed_state.name.opacity_mode})",
                        ),
                        click=lambda: self._on_display_options_changed(SegmentationOpacityEnum.FILL),
                        height=35,
                        prepend_icon="mdi-circle",
                        rounded=0,
                        text="Filled",
                        variant="text",
                    )
                    VBtn(
                        active=(
                            "["
                            f"{self._typed_state.encode(SegmentationOpacityEnum.OUTLINE)}, {self._typed_state.encode(SegmentationOpacityEnum.BOTH)}"
                            f"].includes({self._typed_state.name.opacity_mode})",
                        ),
                        click=lambda: self._on_display_options_changed(SegmentationOpacityEnum.OUTLINE),
                        height=35,
                        prepend_icon="mdi-circle-outline",
                        rounded=0,
                        text="Outlined",
                        variant="text",
                    )

                    ControlButton(
                        icon="mdi-video-3d",
                        name="Toggle 3D",
                        click=f"{self._typed_state.name.show_3d} = ! {self._typed_state.name.show_3d}",
                        active=(self._typed_state.name.show_3d,),
                    )

                Text("Opacity", subtitle=True)
                Slider(
                    typed_state=self._typed_state.get_sub_state(self._typed_state.name.opacity_2d),
                    prepend_icon="mdi-video-2d",
                )
                Slider(
                    typed_state=self._typed_state.get_sub_state(self._typed_state.name.opacity_3d),
                    prepend_icon="mdi-video-3d",
                )

    def _on_display_options_changed(self, opacity_mode):
        if self._typed_state.data.opacity_mode == opacity_mode:
            return
        if self._typed_state.data.opacity_mode == SegmentationOpacityEnum.BOTH:
            self._typed_state.data.opacity_mode = (
                SegmentationOpacityEnum.FILL
                if opacity_mode == SegmentationOpacityEnum.OUTLINE
                else SegmentationOpacityEnum.OUTLINE
            )
        else:
            self._typed_state.data.opacity_mode = SegmentationOpacityEnum.BOTH
