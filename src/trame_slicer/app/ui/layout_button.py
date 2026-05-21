from dataclasses import dataclass, field

from trame_client.widgets.core import Template
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VCard, VCardText, VMenu, VRadio, VRadioGroup

from .control_button import ControlButton


@dataclass
class LayoutButtonState:
    layout_ids: list[str] = field(default_factory=list)
    current_layout_id: str = "Axial Primary"


class LayoutButton(VMenu):
    def __init__(self, **kwargs):
        super().__init__(location="right", close_on_content_click=True)
        self._typed_state = TypedState(self.state, LayoutButtonState)

        with self:
            with Template(v_slot_activator="{props}"):
                ControlButton(
                    v_bind="props",
                    icon="mdi-view-dashboard",
                    name="Layouts",
                    **kwargs,
                )

            with (
                VCard(),
                VCardText(),
                VRadioGroup(
                    v_model=self._typed_state.name.current_layout_id,
                    classes="mt-0",
                    hide_details=True,
                ),
            ):
                VRadio(
                    v_for=f"layout_id in {self._typed_state.name.layout_ids}",
                    label=("layout_id",),
                    value=("layout_id",),
                )
