import inspect
from collections.abc import Callable
from dataclasses import dataclass

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import VBtn, VProgressCircular, VTooltip

from .flex_container import FlexContainer


@dataclass
class DownloadSceneState:
    loading_busy: bool = False


class DownloadSceneButton(FlexContainer):
    def __init__(self, **kwargs):
        super().__init__(justify="center", row=True, style="width: 50px; height: 50px;", **kwargs)
        self._download_callback: Callable | None = None
        self.typed_state = TypedState(self.state, DownloadSceneState)

        with self:
            VTooltip(
                text="Download Scene",
                activator="parent",
                transition="slide-y-transition",
                location="bottom start",
            )
            VBtn(
                v_if=(f"!{self.typed_state.name.loading_busy}",),
                icon="mdi-file-download",
                click=(
                    f"{self.typed_state.name.loading_busy} = true;"
                    "utils.download('scene.mrb', trigger('"
                    f"{self.server.controller.trigger_name(self._on_download_scene)}"
                    f"', ['{self.typed_state.name.loading_busy}']), 'application/octet-stream')"
                ),
                variant="plain",
                hide_details=True,
                density="compact",
            )
            VProgressCircular(v_else=True, indeterminate=True, size=24)

    def set_download_callback(self, download_callback):
        self._download_callback = download_callback

    async def _on_download_scene(self, is_loading_state_name):
        if self._download_callback is None:
            return None

        try:
            result = self._download_callback()
            if inspect.isawaitable(result):
                result = await result
            return result
        finally:
            self.state[is_loading_state_name] = False
