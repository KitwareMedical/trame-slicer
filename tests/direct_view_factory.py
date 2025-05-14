from __future__ import annotations

from dataclasses import dataclass

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
class _View:
    slicer_view: AbstractViewChild


class DirectViewFactory(IViewFactory):
    def can_create_view(self, _view: ViewLayoutDefinition) -> bool:
        return True

    def _create_view(
        self,
        view: ViewLayoutDefinition,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
    ) -> V:
        if view.type == ViewType.SLICE_VIEW:
            slice_view = SliceView(
                scene,
                app_logic,
                view.singleton_tag,
                scheduled_render_strategy=DirectRendering(),
            )
            if view.properties.orientation:
                slice_view.set_orientation(view.properties.orientation)
            return _View(slice_view)
        if view.type == ViewType.THREE_D_VIEW:
            return _View(
                ThreeDView(
                    scene,
                    app_logic,
                    view.singleton_tag,
                    scheduled_render_strategy=DirectRendering(),
                )
            )
        return None

    def _get_slicer_view(self, view: V) -> AbstractViewChild:
        return view.slicer_view
