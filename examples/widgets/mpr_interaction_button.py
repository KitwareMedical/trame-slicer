from slicer import vtkMRMLApplicationLogic, vtkMRMLScene
from trame_server import Server

from trame_slicer.core import SlicerApp

from .control_button import ControlButton
from .utils import StateId


class MprInteractionButton(ControlButton):
    def __init__(self, server=Server, slicer_app=SlicerApp):
        server.state.setdefault(StateId.is_mpr_interaction_active, False)

        super().__init__(
            name="Toggle MPR interaction",
            icon="mdi-cube-scan",
            click=f"{StateId.is_mpr_interaction_active} = !{StateId.is_mpr_interaction_active}",
        )
        self._server = server
        self._slicer_app = slicer_app

        @self.server.state.change(StateId.is_mpr_interaction_active)
        def set_slice_interactive(*_args, **_kwargs):
            is_interactive = self.state[StateId.is_mpr_interaction_active]
            self._slicer_app.app_logic.SetIntersectingSlicesEnabled(
                vtkMRMLApplicationLogic.IntersectingSlicesVisibility, is_interactive
            )
            self._slicer_app.app_logic.SetIntersectingSlicesEnabled(
                vtkMRMLApplicationLogic.IntersectingSlicesInteractive, is_interactive
            )
            self._slicer_app.app_logic.SetIntersectingSlicesEnabled(
                vtkMRMLApplicationLogic.IntersectingSlicesRotation, is_interactive
            )
            self._slicer_app.app_logic.SetIntersectingSlicesEnabled(
                vtkMRMLApplicationLogic.IntersectingSlicesTranslation, is_interactive
            )
            self._slicer_app.app_logic.SetIntersectingSlicesEnabled(
                vtkMRMLApplicationLogic.IntersectingSlicesThickSlabInteractive, is_interactive
            )

        self._slicer_app.scene.AddObserver(vtkMRMLScene.EndBatchProcessEvent, set_slice_interactive)
