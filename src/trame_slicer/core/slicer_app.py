from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from slicer import (
    vtkMRMLColorLogic,
    vtkMRMLCrosshairNode,
    vtkMRMLScene,
    vtkMRMLSliceNode,
    vtkMRMLSliceViewDisplayableManagerFactory,
    vtkMRMLThreeDViewDisplayableManagerFactory,
    vtkSlicerApplicationLogic,
    vtkSlicerDataModuleLogic,
    vtkSlicerModuleLogic,
    vtkSlicerSegmentationsModuleLogic,
    vtkSlicerSubjectHierarchyModuleLogic,
    vtkSlicerTerminologiesModuleLogic,
    vtkSlicerVolumesLogic,
)
from vtkmodules.vtkCommonCore import vtkCollection, vtkOutputWindow


class SlicerApp:
    """
    Container for the core components of a Slicer application.
    Instantiates the scene, application logic and layout manager.
    Configures the default nodes present in the scene.
    """

    def __init__(self, share_directory: str | None = None):
        from trame_slicer.resources import resources_path

        from .display_manager import DisplayManager
        from .io_manager import IOManager
        from .segmentation_editor import SegmentationEditor
        from .view_manager import ViewManager

        self.share_directory = Path(share_directory or resources_path())

        # Output VTK warnings to console by default
        vtk_out = vtkOutputWindow()
        vtk_out.SetDisplayModeToAlwaysStdErr()
        vtkOutputWindow.SetInstance(vtk_out)

        self.scene = vtkMRMLScene()

        # Add one crosshair to the scene
        # Copied from qSlicerCoreApplication::setMRMLScene
        crosshair = vtkMRMLCrosshairNode()
        crosshair.SetCrosshairName("default")
        self.scene.AddNode(crosshair)

        # Create application logic
        self.app_logic = vtkSlicerApplicationLogic()
        self.app_logic.SetMRMLScene(self.scene)
        self.app_logic.GetColorLogic().SetMRMLScene(self.scene)
        self.app_logic.GetColorLogic().AddDefaultColorNodes()

        self.app_logic.SetSliceLogics(vtkCollection())
        self.app_logic.SetViewLogics(vtkCollection())

        # Connect 3D and 2D view displayable manager factories
        vtkMRMLThreeDViewDisplayableManagerFactory.GetInstance().SetMRMLApplicationLogic(self.app_logic)
        vtkMRMLSliceViewDisplayableManagerFactory.GetInstance().SetMRMLApplicationLogic(self.app_logic)

        # Register builtin module logic
        self._register_builtin_logic()

        # Initialize orientation definitions
        patient_right_is_screen_left = True
        vtkMRMLSliceNode.AddDefaultSliceOrientationPresets(self.scene, patient_right_is_screen_left)

        # initialize view manager responsible for creating new views in the app
        self.view_manager = ViewManager(self.scene, self.app_logic)

        # Initialize display manager
        self.display_manager = DisplayManager(self.view_manager, self.volume_rendering)

        # Initialize segmentation editor
        self.segmentation_editor = SegmentationEditor(self.scene, self.segmentations_logic, self.view_manager)

        # Initialize IO manager
        self.io_manager = IOManager(self.scene, self.app_logic, self.segmentation_editor)

    def _register_builtin_logic(self):
        """
        Register builtin Slicer application  module logic.
        """

        from .markups_logic import MarkupsLogic
        from .volume_rendering import VolumeRendering

        self.color_logic = self.register_module_logic(vtkMRMLColorLogic(), logic_name="Colors")
        self.volume_rendering = VolumeRendering(self)
        self.markups_logic = MarkupsLogic(self)
        self.volumes_logic = self.register_module_logic(vtkSlicerVolumesLogic())
        self.terminologies_logic = self.register_module_logic(
            vtkSlicerTerminologiesModuleLogic(), share_sub_folder="terminologies"
        )
        self.segmentations_logic = self.register_module_logic(vtkSlicerSegmentationsModuleLogic())
        self.subject_hierarchy_logic = self.register_module_logic(vtkSlicerSubjectHierarchyModuleLogic())
        self.data_logic = self.register_module_logic(vtkSlicerDataModuleLogic())

    def register_module_logic(self, logic: vtkSlicerModuleLogic, *, logic_name: str = "", share_sub_folder: str = ""):
        """
        Configure the input module logic with the application scene, logic and share directory.
        Registers the logic to the application logic with the given input logic name if any, module name otherwise.

        :param logic: instance of logic to register
        :param logic_name: name of the logic in the application logic
        :param share_sub_folder: sub folder of the share directory (if no sub folder, common share directory is used)
        :return: instance of logic
        """
        if not logic_name:
            logic_name = self._get_default_logic_name(logic)

        # Try to configure share directory before setting the scene / application logic to avoid warning generations
        share_directory = self.share_directory.joinpath(share_sub_folder) if share_sub_folder else self.share_directory
        with suppress(AttributeError):
            logic.SetModuleShareDirectory(share_directory.as_posix())

        logic.SetMRMLScene(self.scene)
        logic.SetMRMLApplicationLogic(self.app_logic)
        self.app_logic.SetModuleLogic(logic_name, logic)
        return logic

    def _get_default_logic_name(self, logic) -> str:
        logic_name = type(logic).__name__
        for n in ["vtkSlicer", "Module", "Logic"]:
            logic_name = logic_name.replace(n, "")
        return logic_name
