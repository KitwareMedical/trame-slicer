from collections.abc import Callable
from math import floor

from trame.widgets.html import Div, Span
from trame.widgets.vuetify3 import VTextField
from trame_vuetify.widgets.vuetify3 import VBtn, VIcon, VTooltip


class ControlButton(VBtn):
    def __init__(
        self,
        *,
        name: str,
        icon: str | tuple,
        click: Callable | str | None = None,
        size: int = 35,
        **kwargs,
    ) -> None:
        size = size or ""
        super().__init__(
            variant=kwargs.pop("variant", "text"),
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


class FlexContainer(Div):
    def __init__(
        self,
        row: bool = False,
        fill_height: bool = False,
        align: str | None = None,
        justify: str | None = None,
        **kwargs,
    ):
        if align is None and row:
            align = "center"
        kwargs["classes"] = " ".join(
            [
                f"d-flex flex-{'row' if row else 'column'}",
                "fill-height" if fill_height else "",
                f"align-{align}" if align is not None else "",
                f"justify-{justify}" if justify is not None else "",
                kwargs.pop("classes", ""),
            ]
        )
        super().__init__(**kwargs)


class Text(Div):
    def __init__(self, text: str, title: bool = False, subtitle: bool = False, **kwargs) -> None:
        kwargs["classes"] = " ".join(
            [
                kwargs.pop("classes", ""),
                "text-subtitle-1" if title else ("text-subtitle-2" if subtitle else ""),
            ]
        )
        super().__init__(**kwargs)

        with self:
            Span(text)


class TextField(VTextField):
    def __init__(self, **kwargs):
        super().__init__(
            variant="solo",
            hide_details=True,
            flat=True,
            bg_color="transparent",
            **kwargs,
        )
