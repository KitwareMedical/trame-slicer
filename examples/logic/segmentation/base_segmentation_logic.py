from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from trame_server import Server

from examples.ui import SegmentEditorUI
from trame_slicer.core import SlicerApp

from ..base_logic import BaseLogic, T


class BaseSegmentationLogic(BaseLogic[T], Generic[T], ABC):
    @property
    def segmentation_editor(self):
        return self._slicer_app.segmentation_editor

    @abstractmethod
    def set_ui(self, ui: SegmentEditorUI):
        pass

    @property
    def active_effect(self):
        return self.segmentation_editor.active_effect


U = TypeVar("U")


class BaseEffectLogic(BaseSegmentationLogic[T], Generic[T, U], ABC):
    def __init__(self, server: Server, slicer_app: SlicerApp, state_type: type[T], effect_type: type[U]):
        super().__init__(server, slicer_app, state_type)
        self._effect_type = effect_type
        self.segmentation_editor.active_effect_name_changed.connect(self._on_effect_changed)

    def is_active(self) -> bool:
        return isinstance(self.active_effect, self._effect_type)

    @property
    def effect(self) -> U:
        return self.active_effect

    def set_active(self):
        self.segmentation_editor.set_active_effect_type(self._effect_type)

    def _on_effect_changed(self, effect_name: str) -> None:
        pass
