from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
    VBtn,
    VBtnToggle,
    VCard,
    VCardItem,
    VCardText,
    VSlider,
)

from trame_slicer.segmentation import SegmentationOpacityEnum

from ..utils import ControlButton, FlexContainer, Text


@dataclass
class SegmentRenderingState:
    rendering_mode: SegmentationOpacityEnum
    opacity_2d: float = 0.5
    opacity_3d: float = 1.0
    show_3d: bool = False
    rendering_options: list[str] = field(default_factory=lambda: ["filled", "outlined"])
    is_extended: bool = False


class SegmentationRenderingUI(VCard):
    def __init__(self, typed_state: TypedState[SegmentRenderingState], **kwargs):
        super().__init__(**kwargs)

        self._typed_state = typed_state
        self._typed_state.bind_changes({self._typed_state.name.rendering_options: self._on_rendering_options_changed})

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
                    with VBtnToggle(
                        v_model=(self._typed_state.name.rendering_options,),
                        classes="align-center",
                        mandatory=True,
                        multiple=True,
                        rounded=0,
                    ):
                        VBtn(
                            prepend_icon="mdi-circle",
                            text="Filled",
                            value="filled",
                            height=35,
                        )
                        VBtn(
                            prepend_icon="mdi-circle-outline",
                            text="Outlined",
                            value="outlined",
                            height=35,
                        )

                    ControlButton(
                        icon="mdi-video-3d",
                        name="Toggle 3D",
                        click=f"{self._typed_state.name.show_3d} = ! {self._typed_state.name.show_3d}",
                        active=(self._typed_state.name.show_3d,),
                    )

                Text("Opacity", subtitle=True)
                VSlider(
                    v_model=(self._typed_state.name.opacity_2d,),
                    hide_details=True,
                    prepend_icon="mdi-video-2d",
                    min=0.0,
                    max=1.0,
                    step=0.01,
                )
                VSlider(
                    v_model=(self._typed_state.name.opacity_3d,),
                    disabled=(f"!{self._typed_state.name.show_3d}",),
                    hide_details=True,
                    prepend_icon="mdi-video-3d",
                    min=0.0,
                    max=1.0,
                    step=0.01,
                )

    def _on_rendering_options_changed(self, rendering_options):
        if "outlined" in rendering_options:
            if "filled" in rendering_options:
                self._typed_state.data.rendering_mode = SegmentationOpacityEnum.BOTH
            else:
                self._typed_state.data.rendering_mode = SegmentationOpacityEnum.OUTLINE
        else:
            self._typed_state.data.rendering_mode = SegmentationOpacityEnum.FILL
