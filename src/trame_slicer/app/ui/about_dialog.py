from __future__ import annotations

from typing import TYPE_CHECKING

from trame_server.utils.typed_state import TypedState

from trame.widgets.vuetify3 import (
    VBtn,
    VCard,
    VCardActions,
    VCardText,
    VCardTitle,
    VDialog,
    VImg,
)
from trame_slicer import __version__

if TYPE_CHECKING:
    from .viewer_layout import ViewerLayoutState


class AboutDialog:
    def __init__(self, typed_state: TypedState[ViewerLayoutState]) -> None:
        self.typed_state = typed_state

    def create_button(self) -> None:
        VBtn(
            icon="mdi-information-outline",
            title="About trame-slicer",
            click=lambda: self.set_visible(True),
        )

    def create_dialog(self) -> None:
        with VDialog(v_model=(self.typed_state.name.is_about_visible,), max_width=400), VCard(border=True):
            with VCardTitle(classes="d-flex align-center ga-2 border-b bg-black"):
                VImg(
                    src="https://raw.githubusercontent.com/KitwareMedical/SlicerTrame/master/SlicerTrame.png",
                    alt="trame-slicer icon",
                    width=32,
                    height=32,
                    max_width=32,
                    cover=False,
                )
                VCardText(f"trame-slicer v{__version__}", classes="pa-0 text-h6")
            with VCardText(classes="pt-4 pb-1"):
                with VBtn(
                    variant="text",
                    classes="d-flex align-center justify-start my-1 px-0 text-none",
                    click="window.open('https://kitware.github.io/trame/', '_blank', 'noopener,noreferrer')",
                    style="height: 8p;",
                ):
                    VCardText("Powered by trame", classes="pa-0 mr-3 flex-grow-0")
                    VImg(
                        src="https://kitware.github.io/trame/logos/trame-text.svg",
                        alt="trame logo",
                        width=72,
                        height=24,
                        max_width=72,
                        cover=False,
                    )
                with VBtn(
                    variant="text",
                    classes="d-flex align-center justify-start my-1 px-0 text-none",
                    click="window.open('https://www.kitware.com/', '_blank', 'noopener,noreferrer')",
                    style="height: 8p;",
                ):
                    VCardText("© 2026 Kitware Inc.", classes="pa-0 mr-3 flex-grow-0")
                    VImg(
                        src="https://www.kitware.com/favicon.ico",
                        alt="Kitware icon",
                        width=20,
                        height=20,
                        max_width=20,
                        cover=False,
                    )
            with VCardActions(classes="justify-end"):
                VBtn(
                    text="GitHub",
                    prepend_icon="mdi-github",
                    click="window.open('https://github.com/KitwareMedical/trame-slicer', '_blank', 'noopener,noreferrer')",
                    classes="mr-auto",
                )
                VBtn(text="Close", click=lambda: self.set_visible(False), variant="outlined")

    def set_visible(self, is_visible: bool) -> None:
        self.typed_state.data.is_about_visible = is_visible
