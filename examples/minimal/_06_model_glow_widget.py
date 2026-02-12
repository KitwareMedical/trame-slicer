"""
Minimal trame-slicer example showing how to create a custom widget.

Adaptation of https://github.com/KitwareMedical/SlicerLayerDisplayableManager/tree/main/Examples/Python/ModelGlowDM
for the trame-slicer examples.
"""

import sys
from tempfile import TemporaryDirectory
from typing import Any

from LayerDMLib import vtkMRMLLayerDMScriptedPipeline
from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLInteractionEventData,
    vtkMRMLLayerDMPipelineFactory,
    vtkMRMLLayerDMPipelineScriptedCreator,
    vtkMRMLModelNode,
    vtkMRMLNode,
    vtkMRMLScene,
    vtkMRMLScriptedModuleNode,
    vtkMRMLTransformNode,
    vtkMRMLViewNode,
    vtkSlicerLayerDMLogic,
)
from trame.app import TrameApp
from trame_client.widgets.html import Div
from trame_vuetify.ui.vuetify3 import SinglePageLayout
from trame_vuetify.widgets.vuetify3 import VFileInput
from vtk import (
    vtkActor,
    vtkCommand,
    vtkGeneralTransform,
    vtkMath,
    vtkNamedColors,
    vtkOutlineGlowPass,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderStepsPass,
    vtkTransformPolyDataFilter,
)

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories
from trame_slicer.utils import write_client_files_to_dir


class ModelGlowPipeline(vtkMRMLLayerDMScriptedPipeline):
    _glowPass = None
    _basicPasses = None
    _pipeline_creator = None

    def __init__(self):
        super().__init__()

        colors = vtkNamedColors()
        self._glowMapper = vtkPolyDataMapper()
        self._glowActor = vtkActor()
        self._glowActor.SetMapper(self._glowMapper)
        self._glowActor.GetProperty().SetColor(colors.GetColor3d("Magenta"))
        self._glowActor.GetProperty().LightingOff()

        self._modelNode = None
        self._modelTransform = None
        self._polyData = None

    @classmethod
    def _InitGlowPass(cls, renderer: vtkRenderer):
        if cls._glowPass is None:
            cls._basicPasses = vtkRenderStepsPass()
            cls._glowPass = vtkOutlineGlowPass()
            cls._glowPass.SetDelegatePass(cls._basicPasses)

        if renderer is not None:
            renderer.SetPass(cls._glowPass)

    @classmethod
    def IsPipelineNode(cls, node):
        return isinstance(node, vtkMRMLScriptedModuleNode) and node.GetAttribute("PipelineType") == cls._GetClassName()

    @classmethod
    def TryCreatePipeline(
        cls, viewNode: vtkMRMLAbstractViewNode, node: vtkMRMLNode
    ) -> vtkMRMLLayerDMScriptedPipeline | None:
        if not cls.IsPipelineNode(node) or not isinstance(viewNode, vtkMRMLViewNode):
            return None

        return cls()

    @classmethod
    def _GetClassName(cls) -> str:
        return cls.__name__

    def OnRendererAdded(self, renderer: vtkRenderer) -> None:
        if renderer is None:
            return

        self._InitGlowPass(renderer)
        renderer.AddViewProp(self._glowActor)

    def OnRendererRemoved(self, renderer: vtkRenderer) -> None:
        if renderer is None:
            return
        renderer.RemoveViewProp(self._glowActor)

    def GetRenderOrder(self) -> int:
        return 1

    def UpdatePipeline(self):
        self._UpdateMapperConnection()
        self._UpdateActorVisibility()
        self.RequestRender()

    def OnUpdate(self, obj, _eventId, _callData):
        if obj == self._modelNode:
            self._ObserveModelTransformNode()

        self.ResetDisplay()

    def SetDisplayNode(self, node):
        super().SetDisplayNode(node)
        self._ObserveModelNode()

    def CanProcessInteractionEvent(self, eventData: vtkMRMLInteractionEventData) -> tuple[bool, float]:
        # Only process mouse move events to avoid blocking camera interaction on click / drag
        isMouseMoveEvent = eventData.GetType() == vtkCommand.MouseMoveEvent

        if not isMouseMoveEvent or not self._IsModelVisible() or self._polyData is None:
            return False, sys.float_info.max

        pos = eventData.GetWorldPosition()
        glowActorBounds = self._polyData.GetBounds()
        isInBounds = (
            glowActorBounds[0] < pos[0] < glowActorBounds[1]
            and glowActorBounds[2] < pos[1] < glowActorBounds[3]
            and glowActorBounds[4] < pos[2] < glowActorBounds[5]
        )
        distance2 = vtkMath.Distance2BetweenPoints(pos, self._polyData.GetCenter())
        return isInBounds, distance2

    def ProcessInteractionEvent(self, _eventData: vtkMRMLInteractionEventData) -> bool:
        if not self.GetDisplayNode():
            return False

        self.GetDisplayNode().SetAttribute("IsSelected", str(1))
        return True

    def LoseFocus(self, eventData: vtkMRMLInteractionEventData | None) -> None:
        super().LoseFocus(eventData)
        if not self.GetDisplayNode():
            return
        self.GetDisplayNode().SetAttribute("IsSelected", str(0))

    def _UpdateMapperConnection(self):
        modelNode: vtkMRMLModelNode = self._GetModelNode()
        self._polyData = self._TransformPolyData(modelNode.GetPolyData() if modelNode else None)
        self._glowMapper.SetInputData(self._polyData)

    def _TransformPolyData(self, polyData):
        transformNode = self._modelNode.GetParentTransformNode() if self._modelNode else None
        if transformNode is None:
            return polyData
        transformFilter = vtkTransformPolyDataFilter()
        transform = vtkGeneralTransform()
        transformNode.GetTransformToWorld(transform)
        transformFilter.SetTransform(transform)
        transformFilter.SetInputData(polyData)
        transformFilter.Update()
        return transformFilter.GetOutput()

    def _UpdateActorVisibility(self):
        isSelected = bool(self.GetDisplayNode() and int(self.GetDisplayNode().GetAttribute("IsSelected")))
        self._glowActor.SetVisibility(self._IsModelVisible() and isSelected)

    @classmethod
    def CreateGlowNode(cls, modelNode: vtkMRMLModelNode, scene: vtkMRMLScene):
        node = vtkMRMLScriptedModuleNode()
        node.SetAttribute("PipelineType", cls._GetClassName())
        node.SetAttribute("ModelNodeID", modelNode.GetID())
        node.SetAttribute("IsSelected", str(0))
        node = scene.AddNode(node)
        modelNode.AddNodeReferenceID(vtkSlicerLayerDMLogic.GetDisplayRole(), node.GetID())
        return node

    def _IsModelVisible(self) -> bool:
        modelNode = self._GetModelNode()
        if modelNode is None:
            return False
        return bool(modelNode.GetDisplayVisibility())

    def _GetModelNode(self) -> vtkMRMLModelNode | None:
        return self.GetScene().GetNodeByID(self._GetModelNodeID(self.GetDisplayNode()))

    def _ObserveModelNode(self):
        if self._modelNode == self._GetModelNode():
            return

        self.UpdateObserver(self._modelNode, self._GetModelNode())
        self._modelNode = self._GetModelNode()
        self._ObserveModelTransformNode()

    def _ObserveModelTransformNode(self):
        transformNode = self._modelNode.GetParentTransformNode() if self._modelNode else None
        if self._modelTransform == transformNode:
            return

        self.UpdateObserver(self._modelTransform, transformNode, vtkMRMLTransformNode.TransformModifiedEvent)
        self._modelTransform = transformNode

    @classmethod
    def _GetModelNodeID(cls, node):
        if cls.IsPipelineNode(node):
            return node.GetAttribute("ModelNodeID")
        return ""

    @classmethod
    def Register(cls):
        if cls._pipeline_creator is not None:
            return
        cls._pipeline_creator = vtkMRMLLayerDMPipelineScriptedCreator()
        cls._pipeline_creator.SetPythonCallback(cls.TryCreatePipeline)
        vtkMRMLLayerDMPipelineFactory.GetInstance().AddPipelineCreator(cls._pipeline_creator)


class ModelGlowTrameSlicerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server)

        # Slicer application creation
        self._slicer_app = SlicerApp()

        # Remote controlled view factory registration
        register_rca_factories(self._slicer_app.view_manager, self._server)

        # Layout creation and view layout registration
        self._layout_manager = LayoutManager(self._slicer_app.scene, self._slicer_app.view_manager, self._server)

        # Register a layout and set the default view layout
        self._layout_manager.register_layout_dict(LayoutManager.default_grid_configuration())
        self._layout_manager.set_layout("3D Only")
        self._build_ui()

        # Register our custom widget
        ModelGlowPipeline.Register()

    def _build_ui(self):
        with SinglePageLayout(self._server) as self.ui:
            self.ui.root.theme = "dark"

            with self.ui.toolbar:
                self.ui.toolbar.clear()

                with Div(classes="d-flex flex-row align-left mx-4"):
                    VFileInput(
                        change=(
                            "trigger('"
                            f"{self.server.controller.trigger_name(self._load_model_files)}"
                            f"', [$event.target.files])"
                        ),
                        prepend_icon="mdi-file-upload",
                        glow=True,
                        multiple=True,
                        hide_input=True,
                        density="compact",
                    )

            with self.ui.content:
                self._layout_manager.initialize_layout_grid(self.ui)

    async def _load_model_files(self, files: list[dict[str, Any]]) -> None:
        with TemporaryDirectory() as tmp_dir:
            model_files = sorted(write_client_files_to_dir(files, tmp_dir))
            for model_file in model_files:
                model_node = self._slicer_app.io_manager.load_model(model_file)
                model_node.CreateDefaultDisplayNodes()
                ModelGlowPipeline.CreateGlowNode(model_node, self._slicer_app.scene)


if __name__ == "__main__":
    app = ModelGlowTrameSlicerApp()
    app.server.start()
