from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from slicer import vtkMRMLApplicationLogic, vtkMRMLScene
from trame_client.widgets.html import Div
from trame_rca.utils import RcaEncoder, RcaRenderScheduler, RcaViewAdapter
from trame_rca.widgets.rca import RemoteControlledArea
from trame_server import Server
from trame_server.utils.asynchronous import create_task

from trame_slicer.core import ViewManager
from trame_slicer.views import (
    AbstractView,
    AbstractViewChild,
    IViewFactory,
    ScheduledRenderStrategy,
    SliceView,
    ThreeDView,
    ViewLayout,
    ViewLayoutDefinition,
    ViewType,
    create_vertical_slice_view_gutter_ui,
    create_vertical_view_gutter_ui,
)


@dataclass
class RcaView:
    vuetify_view: RemoteControlledArea
    slicer_view: AbstractViewChild
    view_adapter: RcaViewAdapter


def register_rca_factories(
    view_manager: ViewManager,
    server: Server,
    slice_view_ui_f: Callable[[Server, str, AbstractViewChild], None] | None = None,
    three_d_view_ui_f: Callable[[Server, str, AbstractViewChild], None] | None = None,
    rca_encoder: RcaEncoder = RcaEncoder.TURBO_JPEG,
    target_fps: float = 30.0,
    interactive_quality: int = 50,
) -> None:
    """
    Helper function to register all RCA factories to a view manager.
    """
    slice_view_ui_f = slice_view_ui_f or create_vertical_slice_view_gutter_ui
    three_d_view_ui_f = three_d_view_ui_f or create_vertical_view_gutter_ui

    for f_type, populate_view_ui_f in [
        (RemoteSliceViewFactory, slice_view_ui_f),
        (RemoteThreeDViewFactory, three_d_view_ui_f),
    ]:
        view_manager.register_factory(
            f_type(
                server,
                rca_encoder=rca_encoder,
                target_fps=target_fps,
                interactive_quality=interactive_quality,
                populate_view_ui_f=populate_view_ui_f,
            )
        )


class RcaRenderStrategy(ScheduledRenderStrategy):
    def __init__(self, rca_scheduler: RcaRenderScheduler):
        super().__init__()
        self._scheduler = rca_scheduler

    def schedule_render(self):
        super().schedule_render()
        self._scheduler.schedule_render()


class RemoteViewFactory(IViewFactory):
    def __init__(
        self,
        server: Server,
        view_ctor: Callable,
        view_type: ViewType,
        *,
        populate_view_ui_f: (Callable[[Server, str, AbstractViewChild], None] | None) = None,
        target_fps: float | None = None,
        interactive_quality: int | None = None,
        rca_encoder: RcaEncoder | str | None = None,
    ):
        super().__init__()
        self._server = server
        self._view_ctor = view_ctor
        self._view_type = view_type

        self._target_fps = target_fps
        self._interactive_quality = interactive_quality
        self._rca_encoder = rca_encoder
        self._populate_view_ui_f = populate_view_ui_f

    def _get_slicer_view(self, view: RcaView) -> AbstractView:
        return view.slicer_view

    def can_create_view(self, view: ViewLayoutDefinition) -> bool:
        return view.type == self._view_type

    def _create_view(
        self,
        view: ViewLayoutDefinition,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
    ) -> RcaView:
        view_id = view.singleton_tag
        slicer_view: AbstractView = self._view_ctor(
            scene=scene,
            app_logic=app_logic,
            name=view_id,
        )

        slicer_view.set_view_properties(view.properties)

        with ViewLayout(self._server, template_name=view_id) as vuetify_view:
            self._create_vuetify_ui(view_id, slicer_view)

        rca_scheduler = RcaRenderScheduler(
            window=slicer_view.render_window(),
            interactive_quality=self._interactive_quality,
            rca_encoder=self._rca_encoder,
            target_fps=self._target_fps,
        )

        rca_view_adapter = RcaViewAdapter(
            window=slicer_view.render_window(),
            name=view_id,
            scheduler=rca_scheduler,
            do_schedule_render_on_interaction=False,
        )
        slicer_view.set_scheduled_render(RcaRenderStrategy(rca_scheduler))

        async def init_rca():
            # RCA protocol needs to be registered before the RCA adapter can be added to the server
            await self._server.ready
            self._server.controller.rc_area_register(rca_view_adapter)

        create_task(init_rca())
        return RcaView(vuetify_view, slicer_view, rca_view_adapter)

    def _create_vuetify_ui(self, view_id: str, slicer_view: AbstractView):
        with Div(style=("position: relative;width: 100%;height: 100%;overflow: hidden;")):
            RemoteControlledArea(
                name=view_id,
                display="image",
                style="position: relative; width: 100%; height: 100%;",
                send_mouse_move=True,
            )

            if self._populate_view_ui_f is not None:
                self._populate_view_ui_f(self._server, view_id, slicer_view)


class RemoteThreeDViewFactory(RemoteViewFactory):
    def __init__(self, server: Server, **kwargs):
        super().__init__(server, ThreeDView, view_type=ViewType.THREE_D_VIEW, **kwargs)


class RemoteSliceViewFactory(RemoteViewFactory):
    def __init__(self, server: Server, **kwargs):
        super().__init__(server, SliceView, view_type=ViewType.SLICE_VIEW, **kwargs)
