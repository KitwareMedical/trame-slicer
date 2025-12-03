from trame.widgets.html import Div


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
