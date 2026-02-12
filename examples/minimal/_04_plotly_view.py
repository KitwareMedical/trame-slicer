"""
Minimal trame-slicer example showing how to connect plotly with trame-slicer.
Requires pandas and trame-plotly
"""

from dataclasses import dataclass
from enum import Enum
from typing import Generic

import pandas as pd
import plotly.graph_objects as go
from slicer import vtkMRMLApplicationLogic, vtkMRMLScene
from trame.app import TrameApp
from trame.widgets import plotly
from trame_client.widgets.core import AbstractElement
from trame_client.widgets.trame import SizeObserver
from trame_vuetify.ui.vuetify3 import SinglePageLayout

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories
from trame_slicer.views import (
    AbstractView,
    AbstractViewChild,
    IViewFactory,
    Layout,
    LayoutDirection,
    ViewLayout,
    ViewLayoutDefinition,
    ViewProps,
)
from trame_slicer.views.view_factory import V

polar_data = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/polar_dataset.csv")


@dataclass
class PlotlyView(Generic[AbstractViewChild]):
    vuetify_view: AbstractElement


class CustomViews(Enum):
    PLOTLY_VIEW = "Plotly"


def create_polar_fig(width=300, height=300, **_):
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=polar_data["x1"].tolist(),
            theta=polar_data["y"].tolist(),
            mode="lines",
            name="Figure 8",
            line_color="peru",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=polar_data["x2"].tolist(),
            theta=polar_data["y"].tolist(),
            mode="lines",
            name="Cardioid",
            line_color="darkviolet",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=polar_data["x3"].tolist(),
            theta=polar_data["y"].tolist(),
            mode="lines",
            name="Hypercardioid",
            line_color="deepskyblue",
        )
    )

    fig.update_layout(
        # title = 'Mic Patterns',
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        showlegend=False,
        width=width,
        height=height,
    )
    return fig


class PlotlyViewFactory(IViewFactory):
    def __init__(self, server, **_):
        super().__init__()
        self._server = server
        self._empty_view = AbstractView()

    def _get_slicer_view(self, _view: V) -> AbstractViewChild:
        return self._empty_view

    def can_create_view(self, view: ViewLayoutDefinition) -> bool:
        return view.view_type == CustomViews.PLOTLY_VIEW

    def _create_view(
        self,
        view: ViewLayoutDefinition,
        _scene: vtkMRMLScene,
        _app_logic: vtkMRMLApplicationLogic,
    ) -> PlotlyView:
        view_id = view.singleton_tag

        @self._server.state.change("polar_size")
        def update_polar_size(polar_size, **_):
            if polar_size is None:
                return

            self._server.controller.update_polar(create_polar_fig(**polar_size.get("size")))

        with ViewLayout(self._server, template_name=view_id) as vuetify_view, SizeObserver("polar_size"):
            self._server.controller.update_polar = plotly.Figure(
                display_mode_bar=("false",),
            ).update

        return PlotlyView(vuetify_view)


def view_layout_configuration() -> dict[str, Layout]:
    plotly_view = ViewLayoutDefinition("Plotly", CustomViews.PLOTLY_VIEW, ViewProps())

    return {
        "default": Layout(
            LayoutDirection.Horizontal,
            [
                ViewLayoutDefinition.threed_view(),
                Layout(
                    LayoutDirection.Vertical,
                    [plotly_view, (ViewLayoutDefinition.axial_view())],
                ),
            ],
            flex_sizes=["2"],
        )
    }


class PlotlyTrameSlicerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server)

        self._slicer_app = SlicerApp()

        register_rca_factories(self._slicer_app.view_manager, self._server)
        self._slicer_app.view_manager.register_factory(PlotlyViewFactory(self._server))

        self._layout_manager = LayoutManager(self._slicer_app.scene, self._slicer_app.view_manager, self._server)
        self._layout_manager.register_layout_dict(view_layout_configuration())
        self._layout_manager.set_layout("default")

        with SinglePageLayout(self._server) as self.ui, self.ui.content:
            self._layout_manager.initialize_layout_grid(self.ui)


if __name__ == "__main__":
    app = PlotlyTrameSlicerApp()
    app.server.start()
