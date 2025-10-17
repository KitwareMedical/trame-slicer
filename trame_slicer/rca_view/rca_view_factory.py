from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Generic

from slicer import vtkMRMLApplicationLogic, vtkMRMLScene
from trame_client.widgets.html import Div
from trame_rca.utils import RcaEncoder, RcaRenderScheduler, RcaViewAdapter, VtkWindow
from trame_rca.widgets.rca import RemoteControlledArea
from trame_server import Server
from trame_server.utils.asynchronous import create_task
from vtkmodules.vtkCommonCore import vtkCommand

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
class RcaView(Generic[AbstractViewChild]):
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
    blur_fps: float = 10.0,
    interactive_quality: int = 50,
    rca_event_throttle_s: str | float | None = None,
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
                blur_fps=blur_fps,
                interactive_quality=interactive_quality,
                populate_view_ui_f=populate_view_ui_f,
                rca_event_throttle_s=rca_event_throttle_s,
            )
        )


class RcaRenderStrategy(ScheduledRenderStrategy):
    def __init__(self, rca_scheduler: RcaRenderScheduler):
        super().__init__()
        self._scheduler = rca_scheduler

    def schedule_render(self):
        super().schedule_render()
        self._scheduler.schedule_render()


class RcaWindow(VtkWindow):
    """
    RCA Window wrapper fixing resize event for 2D views.
    """

    def process_resize_event(self, width, height):
        super().process_resize_event(width, height)
        self._iren.InvokeEvent(vtkCommand.WindowResizeEvent)


class RemoteViewFactory(IViewFactory):
    def __init__(
        self,
        server: Server,
        view_ctor: Callable,
        view_type: Enum,
        *,
        populate_view_ui_f: Callable[[Server, str, AbstractViewChild], None] | None = None,
        target_fps: float | None = None,
        blur_fps: float | None = None,
        interactive_quality: int | None = None,
        rca_encoder: RcaEncoder | str | None = None,
        rca_event_throttle_s: str | float | None = None,
    ):
        """
        :param server: Trame server.
        :param view_ctor: Callback responsible for creating the actual Slicer view.
        :param view_type: Type of view which can be created by the factory.
        :param populate_view_ui_f: Callback to populate the RCA HTML view.
        :param target_fps: Focused rendering speed.
        :param blur_fps: Out of focus rendering speed.
        :param interactive_quality: Interactive RCA image encoding quality.
        :param rca_encoder: Encoder type to use for RCA image encoding.
        :param rca_event_throttle_s: Number of wait seconds in between two process events. (default = 10ms / 100FPS)
            The rca_event_throttle_s can be made reactive on a trame state to vary throttle depending on the application
            use case. For instance, for segmentation effects, the throttle should be 10ms but for interactions blocking
            the server, throttle can be made slower to avoid server lagging behind interactions (for instance 100ms).
        """
        super().__init__()
        self._server = server
        self._view_ctor = view_ctor
        self._view_type = view_type

        self._target_fps = target_fps
        self._blur_fps = blur_fps
        self._interactive_quality = interactive_quality
        self._rca_encoder = rca_encoder
        self._populate_view_ui_f = populate_view_ui_f
        self._rca_event_throttle_s = rca_event_throttle_s if rca_event_throttle_s is not None else 0.01

    def _get_slicer_view(self, view: RcaView) -> AbstractView:
        return view.slicer_view

    def can_create_view(self, view: ViewLayoutDefinition) -> bool:
        return view.view_type == self._view_type

    def _create_view(
        self,
        view: ViewLayoutDefinition,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
    ) -> RcaView:
        view_id = view.singleton_tag
        translated_view_id = self._server.translator.translate_key(view_id)
        slicer_view: AbstractView = self._view_ctor(
            scene=scene,
            app_logic=app_logic,
            name=view_id,
        )

        slicer_view.set_view_properties(view.properties)

        rca_window = RcaWindow(slicer_view.render_window())
        rca_scheduler = RcaRenderScheduler(
            window=rca_window,
            interactive_quality=self._interactive_quality,
            rca_encoder=self._rca_encoder,
            target_fps=self._target_fps,
        )

        with ViewLayout(self._server, template_name=translated_view_id) as vuetify_view:
            self._create_vuetify_ui(translated_view_id, slicer_view, rca_scheduler)

        rca_view_adapter = RcaViewAdapter(
            window=rca_window,
            name=translated_view_id,
            scheduler=rca_scheduler,
            do_schedule_render_on_interaction=False,
        )
        slicer_view.set_scheduled_render(RcaRenderStrategy(rca_scheduler))

        async def init_rca():
            # RCA protocol needs to be registered before the RCA adapter can be added to the server
            await self._server.ready
            self._server.root_server.controller.rc_area_register(rca_view_adapter)

        create_task(init_rca())
        return RcaView(vuetify_view, slicer_view, rca_view_adapter)

    def _create_vuetify_ui(self, view_id: str, slicer_view: AbstractView, rca_scheduler: RcaRenderScheduler):
        def set_scheduler_fps(fps: float | None) -> None:
            """
            Update the view target FPS to the given input value if the value is not None.
            """
            if fps is None:
                return
            rca_scheduler._target_fps = fps

        def set_focus_fps(*_):
            set_scheduler_fps(self._target_fps)

        def set_blur_fps(*_):
            set_scheduler_fps(self._blur_fps)

        # As views are not yet displayed, configure the views in blur FPS until first hover
        set_blur_fps()

        with Div(style="position: relative; width: 100%; height: 100%; overflow: hidden;"):
            RemoteControlledArea(
                name=view_id,
                display="image",
                style="position: relative; width: 100%; height: 100%;",
                send_mouse_move=True,
                mouseenter=set_focus_fps,
                mouseleave=set_blur_fps,
                event_throttle_ms=(f"Math.ceil(1000.0 * {self._rca_event_throttle_s})",),
            )

            if self._populate_view_ui_f is not None:
                self._populate_view_ui_f(self._server, view_id, slicer_view)


class RemoteThreeDViewFactory(RemoteViewFactory):
    def __init__(self, server: Server, **kwargs):
        super().__init__(server, ThreeDView, view_type=ViewType.THREE_D_VIEW, **kwargs)


class RemoteSliceViewFactory(RemoteViewFactory):
    def __init__(self, server: Server, **kwargs):
        super().__init__(server, SliceView, view_type=ViewType.SLICE_VIEW, **kwargs)
