from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from trame_server.utils.typed_state import TypedState

from ..ui.slider import SliderState

if TYPE_CHECKING:
    from trame_server.core import Server

    from trame_slicer.views.abstract_view import AbstractViewChild
    from trame_slicer.views.slice_view import SliceView


def get_view_trame_id(server: Server, view: AbstractViewChild):
    """
    :return: Trame server translated singleton id for the input view.
    """
    return server.translator.translate_key(view.get_singleton_tag())


def get_view_slider_typed_state(server: Server, view: SliceView) -> TypedState[SliderState]:
    """
    :return: Typed Slider state associated with input view
    """
    return TypedState(server.state, SliderState, namespace=get_view_trame_id(server, view))


def connect_slice_view_slider_to_state(
    server: Server,
    view: SliceView,
    *_,
) -> TypedState[SliderState]:
    slider_state = get_view_slider_typed_state(server, view)

    _is_updating_from_trame = defaultdict(bool)
    _is_updating_from_slicer = defaultdict(bool)

    def _on_view_slider_value_changed(slider_value: float):
        if _is_updating_from_slicer[slider_state.name.value]:
            return

        _is_updating_from_trame[slider_state.name.value] = True
        view.set_slice_value(slider_value)
        _is_updating_from_trame[slider_state.name.value] = False

    def _on_slice_view_modified(_view: SliceView):
        if _is_updating_from_trame[slider_state.name.value]:
            return

        _is_updating_from_slicer[slider_state.name.value] = True
        with server.state:
            slider_state.data.min_value, slider_state.data.max_value = _view.get_slice_range()
            slider_state.data.step = _view.get_slice_step()
            slider_state.data.value = _view.get_slice_value()
        server.state.flush()
        _is_updating_from_slicer[slider_state.name.value] = False

    slider_state.bind_changes({slider_state.name.value: _on_view_slider_value_changed})

    view.modified.connect(_on_slice_view_modified)
    _on_slice_view_modified(view)
    return slider_state
