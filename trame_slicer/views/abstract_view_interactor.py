from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from slicer import vtkMRMLInteractionEventData


class AbstractViewInteractor(ABC):
    def __init__(self):
        self.render_callback: Callable | None = None

    @abstractmethod
    def process_event(self, event_data: vtkMRMLInteractionEventData) -> bool:
        pass

    def trigger_render_callback(self) -> None:
        if self.render_callback:
            self.render_callback()
