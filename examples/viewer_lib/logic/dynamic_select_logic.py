from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from examples.viewer_lib.ui.dynamic_select import DynamicSelectState


class IDynamicSelectItem(ABC):
    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @abstractmethod
    def matches(self, other: IDynamicSelectItem) -> bool:
        pass


T = TypeVar("T", bound=IDynamicSelectItem)


class AbstractDynamicSelectLogic(ABC, Generic[T]):
    """
    Abstract logic handling VSelect with dynamic complex VSelect content and value.
    Not to be used for simple VSelect to static Enum list.

    Deriving classes need to implement:
      - _set_slicer_state: Set Slicer state to input IDynamicSelectItem instance
      - _get_slicer_state: Get current Slicer state as IDynamicSelectItem instance
      - _get_current_items: List of all available items

    Select trame state can be refreshed manually by calling the update_ui_from_slicer method.
    """

    current_index_changed = Signal(int)

    def __init__(self, state: TypedState[DynamicSelectState]):
        self._typed_state = state
        self._typed_state.bind_changes({state.name.current_id: self.current_index_changed})
        self._items: list[T] = []
        self.current_index_changed.connect(self._on_current_index_changed)

    def _on_current_index_changed(self, *_):
        selected = self.get_selected()
        if selected is None:
            return
        self._set_slicer_state(selected)

    def update_available_items(self):
        self._items = self._get_current_items()
        self._typed_state.data.items = self._to_item_list(self._items)

    def update_ui_from_slicer(self):
        self.update_available_items()
        self.select_item(self._get_slicer_state())

    def select_item(self, item: T):
        self._typed_state.data.current_id = self._get_item_id(item)

    @classmethod
    def _to_item_list(cls, values: list[T]) -> list[dict[str, int | str]]:
        return [{"title": v.title, "id": i_value} for i_value, v in enumerate(values)]

    def _get_item_id(self, other: T):
        for i_item, item in enumerate(self._items):
            if item.matches(other):
                return i_item
        return -1

    def get_selected(self) -> T | None:
        i_value = self._typed_state.data.current_id
        if i_value < 0 or i_value >= len(self._items):
            return None
        return self._items[i_value]

    @abstractmethod
    def _set_slicer_state(self, item: T) -> None:
        pass

    @abstractmethod
    def _get_slicer_state(self) -> T:
        pass

    @abstractmethod
    def _get_current_items(self) -> list[T]:
        pass
