from slicer import vtkMRMLApplicationLogic, vtkMRMLScene
from trame_server import Server

from trame_slicer.core import SlicerApp

from ..ui import MprInteractionButton, MprInteractionButtonState
from .base_logic import BaseLogic


class MprInteractionButtonLogic(BaseLogic[MprInteractionButtonState]):
    def __init__(self, server=Server, slicer_app=SlicerApp):
        super().__init__(server, slicer_app, MprInteractionButtonState)
        self.bind_changes({self.name.is_interactive: self._on_slice_interactive_changed})
        self._slicer_app.scene.AddObserver(vtkMRMLScene.EndBatchProcessEvent, self._update_slice_interactive)

    def set_ui(self, ui: MprInteractionButton):
        ui.toggle_clicked.connect(self._on_toggle_clicked)

    def _on_toggle_clicked(self):
        self.data.is_interactive = not self.data.is_interactive

    def _update_slice_interactive(self, *_):
        self._on_slice_interactive_changed(self.data.is_interactive)

    def _on_slice_interactive_changed(self, is_interactive: bool):
        app_logic = self._slicer_app.app_logic
        app_logic.SetIntersectingSlicesEnabled(vtkMRMLApplicationLogic.IntersectingSlicesVisibility, is_interactive)
        app_logic.SetIntersectingSlicesEnabled(vtkMRMLApplicationLogic.IntersectingSlicesInteractive, is_interactive)
        app_logic.SetIntersectingSlicesEnabled(vtkMRMLApplicationLogic.IntersectingSlicesRotation, is_interactive)
        app_logic.SetIntersectingSlicesEnabled(vtkMRMLApplicationLogic.IntersectingSlicesTranslation, is_interactive)
        app_logic.SetIntersectingSlicesEnabled(
            vtkMRMLApplicationLogic.IntersectingSlicesThickSlabInteractive, is_interactive
        )
