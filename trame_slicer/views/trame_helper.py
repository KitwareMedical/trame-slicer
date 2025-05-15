from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from trame_client.widgets.html import Div
from trame_server.core import Server
from trame_vuetify.widgets.vuetify3 import VBtn, VIcon, VSlider, VTooltip

from .abstract_view import AbstractViewChild
from .slice_view import SliceView


@dataclass
class SliderStateId:
    value_id: str
    min_id: str
    max_id: str
    step_id: str


def connect_slice_view_slider_to_state(
    server: Server,
    view: SliceView,
    view_id: str,
) -> SliderStateId:
    slider_id = SliderStateId(
        value_id=f"slider_value_{view_id}",
        min_id=f"slider_min_{view_id}",
        max_id=f"slider_max_{view_id}",
        step_id=f"slider_step_{view_id}",
    )

    _is_updating_from_trame = defaultdict(bool)
    _is_updating_from_slicer = defaultdict(bool)

    @server.state.change(slider_id.value_id)
    def _on_view_slider_value_changed(*_, **kwargs):
        if _is_updating_from_slicer[slider_id.value_id]:
            return

        _is_updating_from_trame[slider_id.value_id] = True
        view.set_slice_value(kwargs[slider_id.value_id])
        _is_updating_from_trame[slider_id.value_id] = False

    def _on_slice_view_modified(_view: SliceView):
        if _is_updating_from_trame[slider_id.value_id]:
            return

        _is_updating_from_slicer[slider_id.value_id] = True
        with server.state as state:
            (
                state[slider_id.min_id],
                state[slider_id.max_id],
            ) = _view.get_slice_range()
            state[slider_id.step_id] = _view.get_slice_step()
            state[slider_id.value_id] = _view.get_slice_value()
            state.flush()
        _is_updating_from_slicer[slider_id.value_id] = False

    view.add_modified_observer(_on_slice_view_modified)
    _on_slice_view_modified(view)

    return slider_id


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
        slider_id = connect_slice_view_slider_to_state(server, view, view_id)

        VSlider(
            classes="slice-slider",
            hide_details=True,
            theme="dark",
            v_model=(slider_id.value_id,),
            min=(slider_id.min_id,),
            max=(slider_id.max_id,),
            step=(slider_id.step_id,),
            dense=True,
        )
