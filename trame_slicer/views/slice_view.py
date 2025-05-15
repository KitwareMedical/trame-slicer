from __future__ import annotations

from typing import Literal

from slicer import (
    vtkMRMLApplicationLogic,
    vtkMRMLCrosshairDisplayableManager,
    vtkMRMLLightBoxRendererManagerProxy,
    vtkMRMLMarkupsDisplayableManager,
    vtkMRMLModelSliceDisplayableManager,
    vtkMRMLOrientationMarkerDisplayableManager,
    vtkMRMLRulerDisplayableManager,
    vtkMRMLScalarBarDisplayableManager,
    vtkMRMLScene,
    vtkMRMLSegmentationsDisplayableManager2D,
    vtkMRMLSliceLogic,
    vtkMRMLSliceViewDisplayableManagerFactory,
    vtkMRMLTransformsDisplayableManager2D,
    vtkMRMLVolumeGlyphSliceDisplayableManager,
)
from vtkmodules.vtkCommonCore import reference, vtkCommand
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleUser
from vtkmodules.vtkRenderingCore import vtkActor2D, vtkImageMapper, vtkRenderer

from .abstract_view import AbstractView


class SliceRendererManager(vtkMRMLLightBoxRendererManagerProxy):
    """
    In 3D Slicer the image actor is handled by CTK vtkLightBoxRendererManager currently not wrapped in SlicerLib
    This render manager implements a one image actor / mapper for the rendering without lightbox features.

    It combines the vtkLightBoxRendererManager and vtkMRMLLightBoxRendererManagerProxy features.

    :see: https://github.com/commontk/CTK/blob/master/Libs/Visualization/VTK/Core/vtkLightBoxRendererManager.cpp
    :see: qMRMLSliceControllerWidget.cxx
    """

    def __init__(self, view: SliceView):
        super().__init__()
        self.view = view

        # Create Slice image mapper and set its window / level fix to 8bit
        # The window / level setting based on the input vtkImageData is handled by the vtkVolumeDisplayNode
        # The generated image data is RGBA between 0/255
        self.image_mapper = vtkImageMapper()
        self.image_mapper.SetColorWindow(255)
        self.image_mapper.SetColorLevel(127.5)

        self.image_actor = vtkActor2D()
        self.image_actor.SetMapper(self.image_mapper)
        self.image_actor.GetProperty().SetDisplayLocationToBackground()

    def GetRenderer(self, _):
        return self.view.first_renderer()

    def SetImageDataConnection(self, imageDataConnection):
        self.image_actor.GetMapper().SetInputConnection(imageDataConnection)
        self.add_slice_actor_to_renderer_if_needed()
        self.image_actor.SetVisibility(bool(imageDataConnection))

    def add_slice_actor_to_renderer_if_needed(self):
        renderer = self.GetRenderer(0)
        if renderer.HasViewProp(self.image_actor):
            return

        renderer.AddViewProp(self.image_actor)


class SliceView(AbstractView):
    def __init__(
        self,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
        name: str,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.first_renderer().GetActiveCamera().ParallelProjectionOn()

        self.overlay_renderer = vtkRenderer()
        self.overlay_renderer.GetActiveCamera().ParallelProjectionOn()
        self.overlay_renderer.SetLayer(1)
        self.render_window().SetNumberOfLayers(2)
        self.render_window().AddRenderer(self.overlay_renderer)
        self.render_window().SetAlphaBitPlanes(1)

        # Observe interactor resize event as window resize event is triggered before the window is actually resized.
        self.interactor().AddObserver(vtkCommand.WindowResizeEvent, self._update_slice_size)

        # Add Render manager
        self.render_manager = SliceRendererManager(self)

        self.image_data_connection = None

        factory = vtkMRMLSliceViewDisplayableManagerFactory.GetInstance()
        factory.SetMRMLApplicationLogic(app_logic)

        managers = [
            vtkMRMLCrosshairDisplayableManager.__name__,
            vtkMRMLVolumeGlyphSliceDisplayableManager.__name__,
            vtkMRMLModelSliceDisplayableManager.__name__,
            vtkMRMLOrientationMarkerDisplayableManager.__name__,
            vtkMRMLRulerDisplayableManager.__name__,
            vtkMRMLScalarBarDisplayableManager.__name__,
            vtkMRMLSegmentationsDisplayableManager2D.__name__,
            vtkMRMLMarkupsDisplayableManager.__name__,
            vtkMRMLTransformsDisplayableManager2D.__name__,
        ]

        for manager in managers:
            if not factory.IsDisplayableManagerRegistered(manager):
                factory.RegisterDisplayableManager(manager)

        self.displayable_manager_group.SetLightBoxRendererManagerProxy(self.render_manager)
        self.displayable_manager_group.Initialize(factory, self.renderer())
        self.name = name

        # Create slice logic
        self.logic = vtkMRMLSliceLogic()
        self.logic.SetMRMLApplicationLogic(app_logic)
        self.logic.AddObserver(vtkCommand.ModifiedEvent, self._on_slice_logic_modified_event)
        self._modified_dispatcher.attach_vtk_observer(self.logic, "ModifiedEvent")
        app_logic.GetSliceLogics().AddItem(self.logic)

        # Connect to scene
        self.set_mrml_scene(scene)
        self.interactor().SetInteractorStyle(vtkInteractorStyleUser())

    def _reset_node_view_properties(self):
        super()._reset_node_view_properties()
        if not self.mrml_view_node:
            return

        with self.trigger_modified_once():
            self._call_if_value_not_none(self.mrml_view_node.SetOrientation, self._view_properties.orientation)
            self.mrml_view_node.SetOrientationToDefault()
            self.logic.RotateSliceToLowestVolumeAxes(False)

    def set_mrml_scene(self, scene: vtkMRMLScene) -> None:
        super().set_mrml_scene(scene)
        self.logic.SetMRMLScene(scene)
        if self.mrml_view_node is None:
            self.set_mrml_view_node(self.logic.AddSliceNode(self.name))

    def _on_slice_logic_modified_event(self, *_):
        self._update_image_data_connection()

    def _update_image_data_connection(self):
        self._set_image_data_connection(self.logic.GetImageDataConnection())

    def _set_image_data_connection(self, connection):
        if self.image_data_connection == connection:
            return

        self.image_data_connection = connection
        self.render_manager.SetImageDataConnection(self.image_data_connection)

    def _update_slice_size(self, *_):
        self.logic.ResizeSliceNode(*self.render_window().GetSize())

    def set_orientation(
        self,
        orientation: Literal["Coronal", "Sagittal", "Axial"],
    ) -> None:
        self.mrml_view_node.SetOrientation(orientation)

    def get_orientation(self) -> str:
        return self.mrml_view_node.GetOrientation()

    def fit_view_to_content(self) -> None:
        self.logic.FitSliceToBackground()
        self.logic.SnapSliceOffsetToIJK()

    def set_background_volume_id(self, volume_id: str | None) -> None:
        self.logic.GetSliceCompositeNode().SetBackgroundVolumeID(volume_id)

    def get_background_volume_id(self) -> str | None:
        return self.logic.GetSliceCompositeNode().GetBackgroundVolumeID()

    def set_foreground_volume_id(self, volume_id: str | None) -> None:
        self.logic.GetSliceCompositeNode().SetForegroundVolumeID(volume_id)

    def get_foreground_volume_id(self) -> str | None:
        return self.logic.GetSliceCompositeNode().GetForegroundVolumeID()

    def get_slice_range(self) -> tuple[float, float]:
        (range_min, range_max), _ = self._get_slice_range_resolution()
        return range_min, range_max

    def get_slice_step(self) -> float:
        _, resolution = self._get_slice_range_resolution()
        return resolution

    def _get_slice_range_resolution(self) -> tuple[list[float], float]:
        slice_range = [-1.0, -1.0]
        resolution = reference(1.0)

        if not self.logic.GetSliceOffsetRangeResolution(slice_range, resolution):
            return [0, 1], 0.1
        return slice_range, resolution.get()

    def get_slice_value(self) -> float:
        return self.logic.GetSliceOffset()

    def set_slice_value(self, value: float) -> None:
        if value == self.get_slice_value():
            return

        with self.trigger_modified_once():
            self.logic.SetSliceOffset(value)

    def set_visible_in_3d(self, is_visible: bool):
        self.mrml_view_node.SetSliceVisible(is_visible)

    def is_visible_in_3d(self) -> bool:
        return self.mrml_view_node.GetSliceVisible()

    def toggle_visible_in_3d(self):
        self.set_visible_in_3d(not self.is_visible_in_3d())

    def zoom(self, factor: float):
        """
        Changes the current view field of view by multiplying by input factor.
        :param factor: Values between -inf and 1. Values greater than 0 will zoom in, below 0 will zoom out
        """
        fov_factor = 1 - factor
        if fov_factor <= 0:
            return

        current_fov = self.mrml_view_node.GetFieldOfView()
        self.mrml_view_node.SetFieldOfView(current_fov[0] * fov_factor, current_fov[1] * fov_factor, current_fov[2])

    def zoom_in(self):
        self.zoom(0.2)

    def zoom_out(self):
        self.zoom(-0.2)
