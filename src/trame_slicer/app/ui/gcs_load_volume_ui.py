from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState
from trame_vuetify.widgets.vuetify3 import (
    Template,
    VBtn,
    VCard,
    VCardActions,
    VCardText,
    VCardTitle,
    VDialog,
    VForm,
    VTooltip,
)
from undo_stack import Signal

from .flex_container import FlexContainer
from .text_components import TextField


@dataclass
class GCSDialogState:
    is_open: bool = False
    loading_busy: bool = False
    bucket_name: str = ""
    access_token: str = ""
    gcs_path: str = ""


@dataclass
class GCSLoadVolumeState:
    dialog: GCSDialogState = field(default_factory=GCSDialogState)


class GCSLoadVolumeUI(FlexContainer):
    on_load_volume = Signal(str, str, str)

    def __init__(self, **kwargs):
        kwargs = {"align": "center", "style": "width: 50px;", **kwargs}
        super().__init__(**kwargs)

        typed_state = TypedState(self.state, GCSLoadVolumeState)

        with self:
            self.gcs_load_dialog = GCSDialog(typed_state=typed_state.get_sub_state(typed_state.name.dialog))

        self.gcs_load_dialog.on_load_volume.connect(self.on_load_volume)


class GCSDialog(VDialog):
    on_load_volume = Signal(str, str, str)

    def __init__(self, typed_state: TypedState[GCSDialogState], **kwargs):
        kwargs = {
            "width": "auto",
            "v_model": typed_state.name.is_open,
            **kwargs,
        }
        super().__init__(**kwargs)

        self._typed_state = typed_state

        with self:
            with (
                Template(v_slot_activator="{ props }"),
            ):
                (VBtn(v_bind="props", icon="mdi-cloud-upload", variant="text", density="compact"),)
                VTooltip(text="Open from Google Cloud Storage", activator="parent")

            with (
                VForm(
                    v_slot="{ isValid }",
                    submit_prevent=(
                        f"{typed_state.name.loading_busy} = true; "
                        f"trigger('{self.ctrl.trigger_name(self._on_load)}')"
                        ".finally(() => {"
                        f"{typed_state.name.loading_busy} = false;"
                        "})"
                    ),
                    __events=[("submit_prevent", "submit.prevent")],
                ),
                VCard(),
            ):
                VCardTitle("Load from Google Cloud Storage", classes="text-center")
                with VCardText(), FlexContainer():
                    TextField(
                        v_model=typed_state.name.bucket_name,
                        prepend_icon="mdi-cloud",
                        label="Bucket Name",
                        variant="solo-filled",
                        density="compact",
                        autocomplete="off",
                        rules=("[ value => !!value ||  'Bucket name required' ]",),
                        hide_details=False,
                    )
                    TextField(
                        v_model=typed_state.name.gcs_path,
                        prepend_icon="mdi-folder",
                        label="Object Path (e.g. data/volume.nrrd)",
                        variant="solo-filled",
                        density="compact",
                        autocomplete="off",
                        rules=("[ value => !!value ||  'Object path required' ]",),
                        hide_details=False,
                    )
                    TextField(
                        v_model=typed_state.name.access_token,
                        prepend_icon="mdi-key-chain-variant",
                        label="Access Token (optional)",
                        type="password",
                        variant="solo-filled",
                        density="compact",
                        autocomplete="off",
                        hide_details=False,
                    )
                with VCardActions(classes="justify-end"):
                    VBtn(
                        prepend_icon="mdi-close",
                        text="Cancel",
                        click=self._on_cancel,
                        flat=True,
                    )
                    VBtn(
                        color="primary",
                        disabled=("!isValid.value",),
                        prepend_icon="mdi-cloud-upload",
                        loading=(typed_state.name.loading_busy,),
                        text="Load",
                        variant="tonal",
                        flat=True,
                        __properties=["type"],
                        type="submit",
                    )

    async def _on_load(self):
        await self.on_load_volume.async_emit(
            self._typed_state.data.bucket_name,
            self._typed_state.data.gcs_path,
            self._typed_state.data.access_token,
        )

    def _on_cancel(self):
        self._typed_state.set_dataclass(GCSDialogState())
