from dataclasses import dataclass
from typing import Generic

from slicer import vtkMRMLApplicationLogic, vtkMRMLScene

from .abstract_view import AbstractViewChild
from .render_scheduler import DirectRendering
from .slice_view import SliceView
from .threed_view import ThreeDView
from .view_factory import IViewFactory, V
from .view_layout_definition import ViewLayoutDefinition, ViewType


@dataclass
class _View(Generic[AbstractViewChild]):
    slicer_view: AbstractViewChild


class DirectViewFactory(IViewFactory):
    """
    Creates views in serverless mode with a DirectRendering render scheduler.
    """

    def __init__(self, do_render_offscreen: bool = False):
        super().__init__()
        self._do_render_offscreen = do_render_offscreen

    def can_create_view(self, view: ViewLayoutDefinition) -> bool:
        return view.view_type in [ViewType.SLICE_VIEW, ViewType.THREE_D_VIEW]

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
        return self._update_view_properties(
            ThreeDView(
                scene,
                app_logic,
                view.singleton_tag,
                scheduled_render_strategy=DirectRendering(),
            ),
            view,
        )

    def _create_slice_view(self, app_logic, scene, view: ViewLayoutDefinition) -> SliceView:
        slice_view = SliceView(
            scene,
            app_logic,
            view.singleton_tag,
            scheduled_render_strategy=DirectRendering(),
        )
        return self._update_view_properties(slice_view, view)

    def _get_slicer_view(self, view: V) -> AbstractViewChild:
        return view.slicer_view

    def _update_view_properties(
        self, view_instance: AbstractViewChild, view: ViewLayoutDefinition
    ) -> AbstractViewChild:
        view_instance.render_window().SetOffScreenRendering(self._do_render_offscreen)
        view_instance.set_view_properties(view.properties)
        return view_instance
