from trame.widgets.html import Div, Span
from trame.widgets.vuetify3 import VTextField


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
