from __future__ import annotations

from sys import float_info
from typing import TYPE_CHECKING, TypeVar

from slicer import vtkMRMLAbstractDisplayableManager, vtkMRMLInteractionEventData
from vtkmodules import vtkRenderingCore
from vtkmodules.vtkCommonCore import reference as vtkref
from vtkmodules.vtkCommonCore import vtkCommand

from .abstract_view_interactor import AbstractViewInteractor

if TYPE_CHECKING:
    from .abstract_view import AbstractViewChild


ViewInteractionDispatchChild = TypeVar("ViewInteractionDispatchChild", bound="ViewInteractionDispatch")


class ViewInteractionDispatch:
    """
    Responsible for dispatching the events between user interactors and displayable managers.
    If the user interactors can handle the events, no event is sent to the displayable managers.
    """

    def __init__(self, view: AbstractViewChild):
        self._view = view
        self._user_interactor: list[AbstractViewInteractor] = []
        self._focused_displayable_manager: vtkMRMLAbstractDisplayableManager | None = None

        self._add_observers()

    def add_user_interactor(self, observer: AbstractViewInteractor):
        self._user_interactor.append(observer)

    def remove_user_interactor(self, observer: AbstractViewInteractor):
        self._user_interactor.remove(observer)

    def process_event_data(self, event_data: vtkMRMLInteractionEventData):
        position = self._view.interactor().GetEventPosition()
        poked_renderer = self._view.interactor().FindPokedRenderer(position[0], position[1])
        origin = poked_renderer.GetOrigin()

        event_data.SetDisplayPosition([position[0] - origin[0], position[1] - origin[1]])
        event_data.SetMouseMovedSinceButtonDown(True)
        event_data.SetAttributesFromInteractor(self._view.interactor())
        event_data.SetRenderer(poked_renderer)

    def _add_observers(self):
        iren = self._view.interactor()

        commands = [
            vtkCommand.MouseMoveEvent,
            vtkCommand.RightButtonDoubleClickEvent,
            vtkCommand.RightButtonPressEvent,
            vtkCommand.RightButtonReleaseEvent,
            vtkCommand.MiddleButtonDoubleClickEvent,
            vtkCommand.MiddleButtonPressEvent,
            vtkCommand.MiddleButtonReleaseEvent,
            vtkCommand.LeftButtonDoubleClickEvent,
            vtkCommand.LeftButtonPressEvent,
            vtkCommand.LeftButtonReleaseEvent,
            vtkCommand.EnterEvent,
            vtkCommand.LeaveEvent,
            vtkCommand.MouseWheelForwardEvent,
            vtkCommand.MouseWheelBackwardEvent,
            vtkCommand.StartPinchEvent,
            vtkCommand.PinchEvent,
            vtkCommand.EndPinchEvent,
            vtkCommand.StartRotateEvent,
            vtkCommand.RotateEvent,
            vtkCommand.EndRotateEvent,
            vtkCommand.StartPanEvent,
            vtkCommand.PanEvent,
            vtkCommand.EndPanEvent,
            vtkCommand.TapEvent,
            vtkCommand.LongTapEvent,
            vtkCommand.KeyPressEvent,
            vtkCommand.KeyReleaseEvent,
            vtkCommand.CharEvent,
            vtkCommand.ExposeEvent,
            vtkCommand.ConfigureEvent,
        ]

        for command in commands:
            iren.AddObserver(command, self._event_delegate, 0.0)

    def _event_delegate(self, _caller, ev):
        event_id = vtkCommand.GetEventIdFromString(ev)

        # Fill event data information
        event_data = vtkMRMLInteractionEventData()
        event_data.SetType(event_id)
        self.process_event_data(event_data)

        # Then let user interactor process it. They can abort event processing earlier.
        for interactor in self._user_interactor:
            if interactor.process_event(event_data):
                return

        processed = self._delegate_interaction_event_data_to_displayable_managers(event_data)
        iren_state = self._view.interactor().GetInteractorStyle().GetState()
        if not processed or iren_state != vtkRenderingCore.VTKIS_NONE:
            self._process_events(event_id)

    def _delegate_interaction_event_data_to_displayable_managers(self, event_data: vtkMRMLInteractionEventData):
        dm_group = self._view.displayable_manager_group
        manager_count = dm_group.GetDisplayableManagerCount()
        if manager_count == 0:
            return None

        # Invalidate display position if 3D event
        if event_data.GetType() in [vtkCommand.Button3DEvent, vtkCommand.Move3DEvent]:
            event_data.SetDisplayPositionInvalid()

        # Find the most suitable displayable manager
        closest_distance = float_info.max
        closest_displayable_manager: vtkMRMLAbstractDisplayableManager | None = None
        for i in range(manager_count):
            manager = dm_group.GetNthDisplayableManager(i)
            if manager is None:
                continue
            distance = vtkref(float_info.max)
            if manager.CanProcessInteractionEvent(event_data, distance) and (
                not closest_displayable_manager or distance < closest_distance
            ):
                closest_displayable_manager = manager
                closest_distance = distance

        if not closest_displayable_manager:
            # None of the displayable managers can process the event, just ignore it
            return False

        # Notify displayable managers about focus change
        if self._focused_displayable_manager != closest_displayable_manager:
            if self._focused_displayable_manager is not None:
                self._focused_displayable_manager.SetHasFocus(False, event_data)
            self._focused_displayable_manager = closest_displayable_manager
            if self._focused_displayable_manager is not None:
                self._focused_displayable_manager.SetHasFocus(True, event_data)

        # Process event with new displayable manager
        if self._focused_displayable_manager is None:
            return False

        # This prevents desynchronized update of displayable managers during user interaction
        # (ie. slice intersection widget or segmentations lagging behind during slice translation)
        app_logic = self._focused_displayable_manager.GetMRMLApplicationLogic()
        if app_logic is not None:
            self._focused_displayable_manager.GetMRMLApplicationLogic().PauseRender()

        try:
            return self._focused_displayable_manager.ProcessInteractionEvent(event_data)
        finally:
            if app_logic is not None:
                self._focused_displayable_manager.GetMRMLApplicationLogic().ResumeRender()

    def _process_events(self, event_id):
        style = self._view.interactor_style()
        if not style:
            return

        jump_table = {
            int(vtkCommand.MouseMoveEvent): style.OnMouseMove,
            int(vtkCommand.RightButtonDoubleClickEvent): style.OnRightButtonDoubleClick,
            int(vtkCommand.RightButtonPressEvent): style.OnRightButtonDown,
            int(vtkCommand.RightButtonReleaseEvent): style.OnRightButtonUp,
            int(vtkCommand.MiddleButtonDoubleClickEvent): style.OnMiddleButtonDoubleClick,
            int(vtkCommand.MiddleButtonPressEvent): style.OnMiddleButtonDown,
            int(vtkCommand.MiddleButtonReleaseEvent): style.OnMiddleButtonUp,
            int(vtkCommand.LeftButtonDoubleClickEvent): style.OnLeftButtonDoubleClick,
            int(vtkCommand.LeftButtonPressEvent): style.OnLeftButtonDown,
            int(vtkCommand.LeftButtonReleaseEvent): style.OnLeftButtonUp,
            int(vtkCommand.EnterEvent): style.OnEnter,
            int(vtkCommand.LeaveEvent): style.OnLeave,
            int(vtkCommand.MouseWheelForwardEvent): style.OnMouseWheelForward,
            int(vtkCommand.MouseWheelBackwardEvent): style.OnMouseWheelBackward,
            int(vtkCommand.StartPinchEvent): style.OnStartPinch,
            int(vtkCommand.PinchEvent): style.OnPinch,
            int(vtkCommand.EndPinchEvent): style.OnEndPinch,
            int(vtkCommand.StartRotateEvent): style.OnStartRotate,
            int(vtkCommand.RotateEvent): style.OnRotate,
            int(vtkCommand.EndRotateEvent): style.OnEndRotate,
            int(vtkCommand.StartPanEvent): style.OnStartPan,
            int(vtkCommand.PanEvent): style.OnPan,
            int(vtkCommand.EndPanEvent): style.OnEndPan,
            int(vtkCommand.TapEvent): style.OnTap,
            int(vtkCommand.LongTapEvent): style.OnLongTap,
            int(vtkCommand.KeyPressEvent): style.OnConfigure,
            int(vtkCommand.KeyReleaseEvent): style.OnKeyRelease,
            int(vtkCommand.CharEvent): style.OnChar,
            int(vtkCommand.ExposeEvent): style.OnExpose,
            int(vtkCommand.ConfigureEvent): style.OnConfigure,
        }

        if event_id in jump_table:
            jump_table[event_id]()
