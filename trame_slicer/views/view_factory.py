from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from slicer import vtkMRMLApplicationLogic, vtkMRMLScene

from .abstract_view import AbstractView, AbstractViewChild
from .view_layout_definition import ViewLayoutDefinition

V = TypeVar("V")


class IViewFactory(ABC):
    """
    Interface for view factories.
    """

    def __init__(self):
        self._views: dict[str, V] = {}

    @abstractmethod
    def can_create_view(self, view: ViewLayoutDefinition) -> bool:
        pass

    def create_view(
        self,
        view: ViewLayoutDefinition,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
    ) -> AbstractView:
        self._views[view.singleton_tag] = self._create_view(view, scene, app_logic)
        return self.get_view(view.singleton_tag)

    def remove_view(self, view_id: str) -> bool:
        if not self.has_view(view_id):
            return False

        del self._views[view_id]
        return True

    @abstractmethod
    def _create_view(
        self,
        view: ViewLayoutDefinition,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
    ) -> V:
        """
        Create a new view given the input layout definition and slicer scene / application logic.
        The actual view type returned by this method can be anything.

        The view type will be passed to _get_slicer_view when other classes need to access the underlying slicer
        instance (if any).
        """

    def get_view(self, view_id: str) -> AbstractViewChild | None:
        view = self.get_factory_view(view_id)
        if view is None:
            return None
        return self._get_slicer_view(view)

    def get_factory_view(self, view_id) -> V | None:
        if not self.has_view(view_id):
            return None
        return self._views[view_id]

    def get_views(self) -> list[AbstractViewChild]:
        """
        :return: all slicer AbstractView created by the view factory.
        """
        views = [self._get_slicer_view(view) for view in self._views.values()]
        return [view for view in views if isinstance(view, AbstractView)]

    def has_view(self, view_id: str) -> bool:
        return view_id in self._views

    @abstractmethod
    def _get_slicer_view(self, view: V) -> AbstractViewChild | None:
        """
        :param view: View created using the _create_view method
        :return: The slicer view instance attached to the created view. None if no instance is attached.
        """
