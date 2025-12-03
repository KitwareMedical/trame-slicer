from dataclasses import dataclass

from undo_stack import Signal

from .control_button import ControlButton


@dataclass
class MprInteractionButtonState:
    is_interactive: bool = False


class MprInteractionButton(ControlButton):
    toggle_clicked = Signal()

    def __init__(self):
        super().__init__(name="Toggle MPR interaction", icon="mdi-cube-scan", click=self.toggle_clicked)
