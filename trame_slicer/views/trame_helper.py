from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from trame_client.widgets.html import Div
from trame_server.core import Server
from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VIcon, VTooltip

from ..ui import Slider, SliderState
from .abstract_view import AbstractViewChild
from .slice_view import SliceView


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


def create_vertical_view_gutter_ui(
    server: Server,
    view_id: str,
    view: AbstractViewChild,
    fill_gutter_f: Callable[[Server, str, AbstractViewChild], None] | None = None,
) -> None:
    with (
        Div(
            classes="view-gutter",
            style="position: absolute;top: 0;left: 0;background-color: transparent;height: 100%;",
        ),
        Div(classes="view-gutter-content d-flex flex-column fill-height pa-2"),
    ):
        with VBtn(
            size="medium",
            variant="text",
            click=view.reset_view,
        ):
            VIcon(
                icon="mdi-camera-flip-outline",
                size="medium",
                color="white",
            )
            VTooltip(
                "Reset Camera",
                activator="parent",
                location="right",
                transition="slide-x-transition",
            )

        if fill_gutter_f is not None:
            fill_gutter_f(server, view_id, view)


def create_slice_buttons(_server, _view_id, view: SliceView):
    with VBtn(
        size="medium",
        variant="text",
        click=view.toggle_visible_in_3d,
    ):
        VIcon(
            icon="mdi-video-3d",
            size="medium",
            color="white",
        )
        VTooltip(
            "Show in 3D",
            activator="parent",
            location="right",
            transition="slide-x-transition",
        )


def create_vertical_slice_view_gutter_ui(
    server: Server,
    view_id: str,
    view: AbstractViewChild,
) -> None:
    create_vertical_view_gutter_ui(server, view_id, view, create_slice_buttons)

    with Div(
        classes="slice-slider-gutter",
        style="position: absolute;bottom: 0;left: 0;background-color: transparent;width: 100%;",
    ):
        slider_state = connect_slice_view_slider_to_state(server, view)

        Slider(
            classes="slice-slider",
            typed_state=slider_state,
            theme="dark",
            dense=True,
        )
