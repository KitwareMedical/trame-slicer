from dataclasses import dataclass, field

from trame.widgets.html import Div
from trame.widgets.vuetify3 import (
    Template,
    VBtn,
    VCard,
    VCardActions,
    VCardText,
    VDialog,
    VForm,
    VIcon,
    VSpacer,
    VTooltip,
    VTreeview,
)
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from .flex_container import FlexContainer
from .text_components import TextField


@dataclass
class GCSBucketItem:
    title: str
    value: str
    children: list["GCSBucketItem"] | None


@dataclass
class GCSBucketSearchState:
    loading_busy: bool = False
    bucket_name: str | None = None


@dataclass
class GCSBucketBrowseState:
    loading_busy: bool = False
    bucket_items: list[GCSBucketItem] = field(default_factory=list)
    selected_items: list[str] = field(default_factory=list)


@dataclass
class GCSLoadVolumeState:
    is_dialog_open: bool = False
    bucket_name: str | None = None
    bucket_connected: bool = False
    bucket_search: GCSBucketSearchState = field(default_factory=GCSBucketSearchState)
    bucket_browse: GCSBucketBrowseState = field(default_factory=GCSBucketBrowseState)


class GCSLoadVolumeUI(FlexContainer):
    on_browse_bucket = Signal(str)
    on_load_volume = Signal(str, list)

    def __init__(self, choose_bucket: bool = False, **kwargs):
        kwargs = {"align": "center", "style": "width: 50px;", **kwargs}
        super().__init__(**kwargs)

        typed_state = TypedState(self.state, GCSLoadVolumeState)

        with self:
            self.gcs_load_dialog = GCSDialog(typed_state=typed_state, choose_bucket=choose_bucket)

        self.gcs_load_dialog.on_browse_bucket.connect(self.on_browse_bucket)
        self.gcs_load_dialog.on_load_volume.connect(self.on_load_volume)


class GCSBucketSearch(VCard):
    browse_clicked = Signal(str)
    cancel_clicked = Signal()

    def __init__(self, typed_state: TypedState[GCSBucketSearchState], **kwargs):
        super().__init__(**kwargs)

        with (
            self,
            VForm(
                submit_prevent=(
                    f"{typed_state.name.loading_busy} = true; "
                    f"trigger('{self.ctrl.trigger_name(self.browse_clicked.async_emit)}')"
                    ".finally(() => {"
                    f"{typed_state.name.loading_busy} = false;"
                    "})"
                ),
                __events=[("submit_prevent", "submit.prevent")],
            ),
        ):
            with VCardText():
                TextField(
                    v_model=typed_state.name.bucket_name,
                    prepend_icon="mdi-cloud",
                    label="Bucket Name",
                    density="compact",
                    autocomplete="off",
                    rules=("[ value => !!value ||  'Bucket name required' ]",),
                    hide_details=False,
                    hint="Press Enter to list the bucket content",
                )

            with VCardActions(classes="justify-end"):
                VBtn(
                    click=self.cancel_clicked,
                    flat=True,
                    prepend_icon="mdi-close",
                    text="Cancel",
                )
                VBtn(
                    "Open",
                    disabled=(f"!{typed_state.name.bucket_name}",),
                    flat=True,
                    loading=(typed_state.name.loading_busy,),
                    prepend_icon="mdi-folder",
                    type="submit",
                    variant="tonal",
                    __properties=["type"],
                )


class GCSBucketBrowse(VCard):
    load_clicked = Signal(str)
    cancel_clicked = Signal()

    def __init__(self, typed_state: TypedState[GCSBucketBrowseState], bucket_name: str, **kwargs):
        super().__init__(**kwargs)

        with self:
            with VCardText():
                with FlexContainer(row=True, justify="space-between"):
                    Div(f"{{{{ {bucket_name} }}}}")
                    self.actions_slot = FlexContainer(row=True)

                VTreeview(
                    v_model_selected=typed_state.name.selected_items,
                    density="compact",
                    height=300,
                    items_registration="props",
                    items=(typed_state.name.bucket_items,),
                    select_strategy="classic",
                    selectable=True,
                    __properties=[("v_model_selected", "v_model:selected")],
                )

            with VCardActions():
                Div(
                    f"{{{{ {typed_state.name.selected_items}.length }}}} files selected",
                )
                with VBtn(
                    v_if=f"{typed_state.name.selected_items}.length",
                    click=f"{typed_state.name.selected_items} = [];",
                    density="compact",
                    icon=True,
                ):
                    VIcon(icon="mdi-close-circle")
                    VTooltip(text="Clear selection", activator="parent")
                VSpacer()
                VBtn(
                    click=self.cancel_clicked,
                    flat=True,
                    prepend_icon="mdi-close",
                    text="Cancel",
                )
                VBtn(
                    "Load",
                    click=(
                        f"{typed_state.name.loading_busy} = true; "
                        f"trigger('{self.ctrl.trigger_name(self.load_clicked.async_emit)}')"
                    ),
                    disabled=(f"!{typed_state.name.selected_items}.length",),
                    flat=True,
                    loading=(typed_state.name.loading_busy,),
                    prepend_icon="mdi-cloud-download",
                    variant="tonal",
                )


class GCSDialog(VDialog):
    on_browse_bucket = Signal(str)
    on_load_volume = Signal(str, list)

    def __init__(self, typed_state: TypedState[GCSLoadVolumeState], choose_bucket: bool, **kwargs):
        kwargs = {
            "width": 600,
            "v_model": typed_state.name.is_dialog_open,
            **kwargs,
        }
        super().__init__(**kwargs)

        self._typed_state = typed_state

        with self:
            with Template(v_slot_activator="{ props }"):
                VBtn(
                    v_bind="props",
                    icon="mdi-cloud-upload",
                    variant="text",
                    density="compact",
                )
                VTooltip(
                    text="Open from Google Cloud Storage",
                    activator="parent",
                )
            dialog_title = "Load from Google Cloud Storage"

            bucket_browse = GCSBucketBrowse(
                v_if=typed_state.name.bucket_connected,
                title=dialog_title,
                typed_state=typed_state.get_sub_state(typed_state.name.bucket_browse),
                bucket_name=typed_state.name.bucket_name,
            )
            bucket_browse.load_clicked.connect(self._on_load)
            bucket_browse.cancel_clicked.connect(self._on_cancel)

            if choose_bucket:
                bucket_search = GCSBucketSearch(
                    v_if=f"!{typed_state.name.bucket_connected}",
                    title=dialog_title,
                    typed_state=typed_state.get_sub_state(typed_state.name.bucket_search),
                )
                bucket_search.browse_clicked.connect(self._on_browse)
                bucket_search.cancel_clicked.connect(self._on_cancel)

                with bucket_browse.actions_slot, VBtn(click=self._clear_bucket, icon=True, density="compact"):
                    VTooltip(text="Switch GCS bucket", activator="parent")
                    VIcon(icon="mdi-swap-horizontal")

    async def _on_browse(self):
        await self.on_browse_bucket.async_emit(self._typed_state.data.bucket_search.bucket_name)

    async def _on_load(self):
        await self.on_load_volume.async_emit(self._typed_state.data.bucket_browse.selected_items)

    def _clear_bucket(self):
        self._typed_state.set_dataclass(GCSLoadVolumeState(is_dialog_open=True))

    def _on_cancel(self):
        self._typed_state.data.is_dialog_open = False
