from dataclasses import dataclass

from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from .control_button import ControlButton
from .flex_container import FlexContainer


@dataclass
class MprInteractionButtonState:
    is_interactive: bool = False


class MprInteractionButton(FlexContainer):
    toggle_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__()
        typed_state = TypedState(self.state, MprInteractionButtonState)
        with self:
            ControlButton(
                name="Toggle MPR interaction",
                icon="mdi-cube-scan",
                active=(typed_state.name.is_interactive,),
                click=self.toggle_clicked,
                **kwargs,
            )
