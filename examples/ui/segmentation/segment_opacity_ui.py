from dataclasses import dataclass

from trame_client.widgets.html import Span
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VContainer, VRow, VSlider

from trame_slicer.segmentation import SegmentationOpacityEnum


@dataclass
class SegmentOpacityState:
    opacity_mode: SegmentationOpacityEnum = SegmentationOpacityEnum.BOTH
    opacity_icon: str = ""
    opacity_text: str = ""
    opacity_2d: float = 0.5
    opacity_3d: float = 1.0
    is_visible: bool = False


class SegmentationOpacityUI(VContainer):
    def __init__(self, typed_state: TypedState[SegmentOpacityState], **kwargs):
        super().__init__(**kwargs)

        self._typed_state = typed_state
        self._typed_state.bind_changes({self._typed_state.name.opacity_mode: self._on_opacity_mode_change})
        self._on_opacity_mode_change(self._typed_state.data.opacity_mode)

        with self:
            with VRow():
                VBtn(
                    text=(self._typed_state.name.opacity_text,),
                    prepend_icon=(self._typed_state.name.opacity_icon,),
                    click=self._toggle_opacity_mode,
                    block=True,
                    style="text-transform: none;",
                )
            with VRow(align="center"):
                Span("2D")
                VSlider(min=0.0, max=1.0, step=0.01, hide_details=True, v_model=(self._typed_state.name.opacity_2d,))
            with VRow(align="center"):
                Span("3D")
                VSlider(min=0.0, max=1.0, step=0.01, hide_details=True, v_model=(self._typed_state.name.opacity_3d,))

    def _on_opacity_mode_change(self, opacity_mode: SegmentationOpacityEnum) -> None:
        """
        Update opacity mode icon depending on current opacity mode enum.
        """
        self._typed_state.data.opacity_icon = {
            SegmentationOpacityEnum.FILL: "mdi-circle-medium",
            SegmentationOpacityEnum.OUTLINE: "mdi-circle-outline",
            SegmentationOpacityEnum.BOTH: "mdi-circle",
        }.get(opacity_mode, "mdi-circle")

        self._typed_state.data.opacity_text = f"Mode: {opacity_mode.name.title()}"

    def _toggle_opacity_mode(self):
        new_opacity_mode = SegmentationOpacityEnum(self._typed_state.data.opacity_mode).next()
        self._typed_state.data.opacity_mode = new_opacity_mode
