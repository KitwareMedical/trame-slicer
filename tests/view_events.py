from __future__ import annotations

from enum import Enum, auto


class MouseButton(Enum):
    Left = auto()
    Right = auto()
    Middle = auto()


class ButtonEvent(Enum):
    Press = auto()
    Release = auto()


class ViewEvents:
    def __init__(self, view):
        self._view = view

    @property
    def interactor(self):
        return self._view.interactor()

    def mouse_move_to(self, x, y):
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("MouseMoveEvent")

    def _mouse_button_event(self, mouse_button: MouseButton | str, button_event: ButtonEvent | str):
        mouse_button = MouseButton(mouse_button)
        button_event = ButtonEvent(button_event)
        self.interactor.InvokeEvent(f"{mouse_button.name}Button{button_event.name}Event")

    def mouse_press_event(self, mouse_button: MouseButton | str = MouseButton.Left):
        self._mouse_button_event(mouse_button, ButtonEvent.Press)

    def mouse_release_event(self, mouse_button: MouseButton | str = MouseButton.Left):
        self._mouse_button_event(mouse_button, ButtonEvent.Release)

    def click_at_coordinate(self, x, y, *, mouse_button: MouseButton | str = MouseButton.Left):
        self.mouse_move_to(x, y)
        self.mouse_press_event(mouse_button)
        self.mouse_release_event(mouse_button)

    def view_center(self):
        return (
            self._view.render_window().GetSize()[0] // 2,
            self._view.render_window().GetSize()[1] // 2,
        )

    def click_at_center(self):
        self.click_at_coordinate(*self.view_center())

    def key_press(self, key: str):
        self.interactor.SetKeyEventInformation(0, 0, key, 0, key)
        self.interactor.InvokeEvent("KeyPressEvent")
        self.interactor.InvokeEvent("KeyReleaseEvent")
        self.interactor.SetKeyEventInformation(0, 0, " ", 0, " ")
