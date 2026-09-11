"""
Minimal trame-slicer app running on the React client with MUI.

It reuses the `trame_slicer.app.logic` components and only supplies a React UI
(MUI controls, React view gutters and a MUI `SinglePageLayout`): load a volume,
volume-render it in a 3D view and switch layout, preset, shift and markups.

Requires `trame-mui` (not a trame-slicer dependency):

    python examples/minimal/_08_react_mui_volume_rendering.py
"""

from pathlib import Path

from trame.app import TrameApp
from trame.widgets import client, html, react
from trame_mui.ui.mui import SinglePageLayout
from trame_mui.widgets import mui
from undo_stack import Signal

from trame_slicer.app.logic import (
    LayoutButtonLogic,
    LoadVolumeLogic,
    MarkupsButtonLogic,
    VolumePropertyLogic,
    connect_slice_view_slider_to_state,
)
from trame_slicer.core import SlicerApp
from trame_slicer.rca_view import register_rca_factories

SAMPLE_VOLUME = Path(__file__).parent.parent.parent / "tests" / "data" / "mr_head.nrrd"

GUTTER_BUTTON_STYLE = {"color": "white", "backgroundColor": "rgba(0, 0, 0, 0.35)"}
GUTTER_STYLE = {
    "position": "absolute",
    "top": 0,
    "left": 0,
    "display": "flex",
    "flexDirection": "column",
    "alignItems": "center",
    "gap": "4px",
    "padding": "4px",
}
SLIDER_STYLE = {
    "position": "absolute",
    "bottom": 0,
    "left": 0,
    "width": "100%",
    "padding": "0 12px 8px 12px",
    "boxSizing": "border-box",
}


def create_gutter_button(glyph: str, tooltip: str, on_click) -> None:
    with mui.Tooltip(title=tooltip):
        mui.IconButton(
            glyph,
            size="small",
            on_click=react.Callback(on_click),
            style=GUTTER_BUTTON_STYLE,
        )


def create_vertical_view_gutter_ui(server, view_id, view, fill_gutter_f=None) -> None:
    with mui.Box(style=GUTTER_STYLE):
        create_gutter_button("\u27f2", "Reset Camera", view.reset_view)
        if fill_gutter_f is not None:
            fill_gutter_f(server, view_id, view)


def create_slice_buttons(_server, _view_id, view) -> None:
    create_gutter_button("\u25a3", "Show in 3D", view.toggle_visible_in_3d)


def create_slice_slider(server, view) -> None:
    slider = connect_slice_view_slider_to_state(server, view)
    with mui.Box(style=SLIDER_STYLE):
        mui.Slider(
            value=react.Bind(slider.name.value),
            min=react.Bind(slider.name.min_value),
            max=react.Bind(slider.name.max_value),
            step=react.Bind(slider.name.step),
            size="small",
            value_label_display="auto",
            on_change=react.Callback(f"{slider.name.value} = Number($event.target.value)"),
        )


def create_vertical_slice_view_gutter_ui(server, view_id, view) -> None:
    create_vertical_view_gutter_ui(server, view_id, view, create_slice_buttons)
    create_slice_slider(server, view)


class LoadVolumeControls(mui.Stack):
    on_load_volume = Signal(list)

    def __init__(self, **kwargs):
        super().__init__(direction="row", spacing=1, **kwargs)
        with self:
            self._file_button("Open Files", load_directory=False)
            self._file_button("Open Directory", load_directory=True)

    def _file_button(self, name: str, *, load_directory: bool) -> None:
        button = mui.Button(name, variant="outlined", component="label")
        # `component` is a MUI Button prop missing from the generated wrapper.
        button.props += ["component"]
        with button:
            html.Input(
                type="file",
                multiple=True,
                style={"display": "none"},
                on_change=react.Callback(self.on_load_volume, args="[$event.target.files]"),
                **({"webkitdirectory": True} if load_directory else {}),
            )


class MarkupsControls(mui.Stack):
    place_node_type = Signal(str, bool)
    clear_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(direction="row", spacing=1, **kwargs)
        with self:
            self._place_button("Place fiducial", "vtkMRMLMarkupsFiducialNode")
            self._place_button("Place ruler", "vtkMRMLMarkupsLineNode")
            mui.Button("Clear", variant="outlined", on_click=react.Callback(self.clear_clicked))

    def _place_button(self, name: str, node_type: str) -> None:
        mui.Button(
            name,
            variant="outlined",
            on_click=react.Callback(self.place_node_type, args=f"['{node_type}', true]"),
        )


class ReactMuiTrameSlicerApp(TrameApp):
    client_type = "react"

    def __init__(self, server=None):
        super().__init__(server=server, client_type=self.client_type)
        self._slicer_app = SlicerApp()
        register_rca_factories(
            self._slicer_app.view_manager,
            self._server,
            rca_encoder="video",
            slice_view_ui_f=create_vertical_slice_view_gutter_ui,
            three_d_view_ui_f=create_vertical_view_gutter_ui,
        )
        self._setup_logic()
        self._build_ui()
        self._load_sample_volume()

    def _setup_logic(self) -> None:
        self._layout_logic = LayoutButtonLogic(self._server, self._slicer_app)
        self._volume_logic = VolumePropertyLogic(self._server, self._slicer_app)
        self._load_logic = LoadVolumeLogic(self._server, self._slicer_app)
        self._markups_logic = MarkupsButtonLogic(self._server, self._slicer_app)
        self._load_logic.volume_loaded.connect(self._volume_logic.on_volume_changed)
        self._volume_logic.data.preset_3d_name = "MR-Default"

    def _build_ui(self) -> None:
        with SinglePageLayout(self._server, mode="dark") as self.ui:
            client.Style("body { margin: 0; } html { overflow: hidden; }")
            self.ui.title.set_text("trame-slicer + React/MUI")

            with self.ui.toolbar:
                mui.Box(style={"flex": "1"})
                self._load_controls = LoadVolumeControls()
                self._load_logic.set_ui(self._load_controls)
                mui.Button(
                    "Sample",
                    variant="contained",
                    on_click=react.Callback(self._load_sample_volume),
                )

            with (
                self.ui.content,
                mui.Stack(direction="row", style={"height": "100%", "width": "100%"}),
            ):
                with mui.Paper(square=True, style={"width": "300px", "overflowY": "auto"}):
                    self._build_control_panel()
                with mui.Box(style={"flex": "1", "minWidth": 0}):
                    self._layout_logic.layout_manager.initialize_layout_grid(self.ui)

    def _build_control_panel(self) -> None:
        with mui.Stack(spacing=2, style={"padding": "16px"}):
            mui.Typography("Layout", variant="subtitle2", color="text.secondary")
            with mui.Select(
                value=react.Bind(self._layout_logic.name.current_layout_id),
                on_change=react.Callback(f"{self._layout_logic.name.current_layout_id} = $event.target.value"),
                display_empty=True,
                style={"width": "100%"},
            ):
                for layout_id in self._layout_logic.data.layout_ids:
                    mui.MenuItem(layout_id, value=layout_id)

            mui.Divider()
            mui.Typography("3D Preset", variant="subtitle2", color="text.secondary")
            with mui.Select(
                value=react.Bind(self._volume_logic.name.preset_3d_name),
                on_change=react.Callback(f"{self._volume_logic.name.preset_3d_name} = $event.target.value"),
                display_empty=True,
                style={"width": "100%"},
            ):
                for preset in self._volume_logic.data.presets_3d:
                    mui.MenuItem(preset.title, value=preset.title)

            self._build_vr_shift_control()

            mui.Divider()
            self._markups_controls = MarkupsControls()
            self._markups_logic.set_ui(self._markups_controls)

    def _build_vr_shift_control(self) -> None:
        state = self._volume_logic.name.vr_shift_slider
        mui.Typography("Volume Rendering Shift", variant="subtitle2", color="text.secondary")
        mui.Slider(
            value=react.Bind(state.value),
            min=react.Bind(state.min_value),
            max=react.Bind(state.max_value),
            step=react.Bind(state.step),
            value_label_display="auto",
            on_change=react.Callback(f"{state.value} = Number($event.target.value)"),
        )

    def _load_sample_volume(self) -> None:
        if not SAMPLE_VOLUME.is_file():
            return
        volumes = self._slicer_app.io_manager.load_volumes(SAMPLE_VOLUME.as_posix())
        if not volumes:
            return
        self._slicer_app.display_manager.show_volume(volumes[0], do_reset_views=True)
        self._load_logic.volume_loaded.emit(volumes[0])


if __name__ == "__main__":
    ReactMuiTrameSlicerApp().server.start()
