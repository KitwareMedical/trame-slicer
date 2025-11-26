from abc import ABC, abstractmethod

from trame_client.widgets.core import AbstractElement
from trame_server.utils.typed_state import TypedState

from ..viewer_layout import ViewerLayoutState


class AbstractToolUI(AbstractElement, ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Each tool must provide its name.
        """
        raise NotImplementedError

    @abstractmethod
    def build_drawer_ui(self):
        """
        Build UI in the side drawer.
        """
        raise NotImplementedError

    @abstractmethod
    def build_toolbar_ui(self):
        """
        Build UI in the toolbar.
        """
        raise NotImplementedError

    def __init__(self, **kwargs):
        super().__init__(self.name, **kwargs)
        self._viewer_state = TypedState(self.state, ViewerLayoutState)
