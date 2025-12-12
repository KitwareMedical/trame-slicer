from dataclasses import dataclass
from typing import Generic

from slicer import vtkMRMLApplicationLogic, vtkMRMLScene

from trame_slicer.views import (
    AbstractViewChild,
    DirectRendering,
    IViewFactory,
    SliceView,
    ThreeDView,
    ViewLayoutDefinition,
    ViewType,
)
from trame_slicer.views.view_factory import V


@dataclass
class _View(Generic[AbstractViewChild]):
    slicer_view: AbstractViewChild


class DirectViewFactory(IViewFactory):
    def __init__(self, do_render_offscreen: bool):
        super().__init__()
        self._do_render_offscreen = do_render_offscreen

    def can_create_view(self, _view: ViewLayoutDefinition) -> bool:
        return True

    def _create_view(
        self,
        view: ViewLayoutDefinition,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
    ) -> V:
        if view.view_type == ViewType.SLICE_VIEW:
            slice_view = self._create_slice_view(app_logic, scene, view)
            return _View(slice_view)
        if view.view_type == ViewType.THREE_D_VIEW:
            return _View(self._create_threed_view(app_logic, scene, view))
        return None

    def _create_threed_view(self, app_logic, scene, view: ViewLayoutDefinition) -> ThreeDView:
        return self._update_offscreen_rendering(
            ThreeDView(
                scene,
                app_logic,
                view.singleton_tag,
                scheduled_render_strategy=DirectRendering(),
            )
        )

    def _create_slice_view(self, app_logic, scene, view: ViewLayoutDefinition) -> SliceView:
        slice_view = SliceView(
            scene,
            app_logic,
            view.singleton_tag,
            scheduled_render_strategy=DirectRendering(),
        )
        if view.properties.orientation:
            slice_view.set_orientation(view.properties.orientation)
        return self._update_offscreen_rendering(slice_view)

    def _get_slicer_view(self, view: V) -> AbstractViewChild:
        return view.slicer_view

    def _update_offscreen_rendering(self, view: AbstractViewChild) -> AbstractViewChild:
        view.render_window().SetOffScreenRendering(self._do_render_offscreen)
        return view
