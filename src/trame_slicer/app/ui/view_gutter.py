from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from trame_client.widgets.html import Div
from trame_vuetify.widgets.vuetify3 import VBtn, VIcon, VTooltip

from ..logic.slice_view_logic import connect_slice_view_slider_to_state
from .slider import Slider

if TYPE_CHECKING:
    from trame_server.core import Server

    from trame_slicer.views import AbstractViewChild, SliceView


def create_vertical_view_gutter_ui(
    server: Server,
    view_id: str,
    view: AbstractViewChild,
    fill_gutter_f: Callable[[Server, str, AbstractViewChild], None] | None = None,
) -> None:
    with (
        Div(
            classes="view-gutter",
            style="position: absolute;top: 0;left: 0;background-color: transparent;",
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
