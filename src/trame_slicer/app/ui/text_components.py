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
        kwargs["style"] = " ".join(
            [
                "user-select: none;",  # text is not selectable by default
                kwargs.pop("style", ""),
            ]
        )
        super().__init__(**kwargs)

        with self:
            Span(text)


class TextField(VTextField):
    def __init__(self, **kwargs):
        kwargs.setdefault("variant", "solo")
        kwargs.setdefault("hide_details", True)
        kwargs.setdefault("flat", True)
        kwargs.setdefault("bg_color", "transparent")
        super().__init__(**kwargs)
