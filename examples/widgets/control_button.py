from __future__ import annotations

from collections.abc import Callable
from math import floor

from trame_client.widgets.html import Span
from trame_vuetify.widgets.vuetify3 import VBtn, VIcon, VTooltip


class ControlButton(VBtn):
    def __init__(
        self,
        *,
        name: str,
        icon: str,
        click: Callable | None = None,
        size: int = 40,
        **kwargs,
    ) -> None:
        size = size or ""
        super().__init__(
            variant="text",
            rounded=0,
            height=size,
            width=size,
            min_height=size,
            min_width=size,
            click=click,
            **kwargs,
        )

        icon_size = floor(0.6 * size) if size else ""

        with self:
            VIcon(icon, size=icon_size)
            with VTooltip(
                activator="parent",
                transition="slide-x-transition",
                location="right",
            ):
                Span(f"{name}")
