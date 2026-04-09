from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from trame_server.utils.typed_state import TypedState

from examples.viewer_lib.logic import AbstractDynamicSelectLogic, IDynamicSelectItem
from examples.viewer_lib.ui import DynamicSelectState


@dataclass
class _DynSelectItem(IDynamicSelectItem):
    item_content: str = ""

    @property
    def title(self) -> str:
        return f"Title {self.item_content}"

    def matches(self, other: _DynSelectItem) -> bool:
        return self == other


class _DynSelectLogic(AbstractDynamicSelectLogic[_DynSelectItem]):
    def __init__(self, state: TypedState[DynamicSelectState]):
        super().__init__(state)
        self.set_slicer_state_mock = MagicMock()
        self.get_slicer_state_mock = MagicMock(return_value=_DynSelectItem("2"))
        self.get_current_mock = MagicMock(return_value=[_DynSelectItem("1"), _DynSelectItem("2"), _DynSelectItem("3")])

    def _set_slicer_state(self, item: _DynSelectItem):
        self.set_slicer_state_mock(item)

    def _get_slicer_state(self) -> _DynSelectItem:
        return self.get_slicer_state_mock()

    def _get_current_items(self) -> list[_DynSelectItem]:
        return self.get_current_mock()


@pytest.fixture
def select_state(a_state):
    a_state.ready()
    return TypedState(a_state, DynamicSelectState)


@pytest.fixture
def logic(select_state):
    return _DynSelectLogic(select_state)


def test_on_refresh_populates_select_state_with_available(logic, select_state, a_state):
    logic.update_ui_from_slicer()
    a_state.flush()
    assert select_state.data.items == [
        {"title": "Title 1", "id": 0},
        {"title": "Title 2", "id": 1},
        {"title": "Title 3", "id": 2},
    ]
    assert select_state.data.current_id == 1


def test_on_id_change_refreshes_slicer_state(logic, select_state, a_state):
    logic.update_ui_from_slicer()
    a_state.flush()

    logic.set_slicer_state_mock.reset_mock()
    select_state.data.current_id = 2
    a_state.flush()

    assert logic.get_selected() == _DynSelectItem("3")
    logic.set_slicer_state_mock.assert_called_once_with(logic.get_selected())
