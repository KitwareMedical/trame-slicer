from __future__ import annotations

from enum import IntEnum, auto
from typing import Literal

import vtk
from slicer import (
    vtkMRMLApplicationLogic,
    vtkMRMLColorLegendDisplayableManager,
    vtkMRMLCrosshairDisplayableManager,
    vtkMRMLLayerDisplayableManager,
    vtkMRMLLinearTransformsDisplayableManager,
    vtkMRMLMarkupsDisplayableManager,
    vtkMRMLModelSliceDisplayableManager,
    vtkMRMLOrientationMarkerDisplayableManager,
    vtkMRMLRulerDisplayableManager,
    vtkMRMLScalarBarDisplayableManager,
    vtkMRMLScene,
    vtkMRMLSegmentationsDisplayableManager2D,
    vtkMRMLSliceLayerLogic,
    vtkMRMLSliceLogic,
    vtkMRMLSliceViewDisplayableManagerFactory,
    vtkMRMLSliceViewInteractorStyle,
    vtkMRMLTransformsDisplayableManager2D,
    vtkMRMLVolumeGlyphSliceDisplayableManager,
    vtkMRMLVolumeNode,
)
from vtkmodules.vtkCommonCore import reference, vtkCommand
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleUser
from vtkmodules.vtkRenderingCore import vtkActor2D, vtkImageMapper, vtkRenderer

from .abstract_view import AbstractView


class SliceRendererManager:
    """
    In 3D Slicer the image actor is handled by CTK vtkLightBoxRendererManager currently not wrapped in SlicerLib
    This render manager implements a one image actor / mapper for the rendering.
    vtkMRMLLightBoxRendererManagerProxy was removed from Slicer 5.10. This class implements only the
    vtkLightBoxRendererManager feature for displaying the Slice image actor on update.

    :see: https://github.com/commontk/CTK/blob/master/Libs/Visualization/VTK/Core/vtkLightBoxRendererManager.cpp
    :see: qMRMLSliceControllerWidget.cxx
    """

    def __init__(self, view: SliceView):
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

    def SetImageDataConnection(self, imageDataConnection):
        self.image_actor.GetMapper().SetInputConnection(imageDataConnection)
        self._AddSliceActorToRendererIfNeeded()
        self.image_actor.SetVisibility(bool(imageDataConnection))

    def _AddSliceActorToRendererIfNeeded(self):
        renderer = self.view.first_renderer()
        if renderer.HasViewProp(self.image_actor):
            return

        renderer.AddViewProp(self.image_actor)


class SliceLayer(IntEnum):
    """
    Int enum to manage Slice Layers.

    """

    Background = auto()
    Foreground = auto()

    @classmethod
    def as_int(cls, layer: int | SliceLayer) -> int:
        if isinstance(layer, SliceLayer):
            return layer.value
        return layer


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

        self._overlay_renderer = vtkRenderer()
        self._overlay_renderer.GetActiveCamera().ParallelProjectionOn()
        self._overlay_renderer.SetLayer(1)
        self.render_window().SetNumberOfLayers(2)
        self.render_window().AddRenderer(self._overlay_renderer)
        self.render_window().SetAlphaBitPlanes(1)

        # Observe interactor resize event as window resize event is triggered before the window is actually resized.
        self.interactor().AddObserver(vtkCommand.WindowResizeEvent, self._update_slice_size)

        # Add Render manager
        self._render_manager = SliceRendererManager(self)

        self._image_data_connection = None
        self._interactor_observer = vtkMRMLSliceViewInteractorStyle()

        managers = [
            vtkMRMLCrosshairDisplayableManager,
            vtkMRMLVolumeGlyphSliceDisplayableManager,
            vtkMRMLModelSliceDisplayableManager,
            vtkMRMLOrientationMarkerDisplayableManager,
            vtkMRMLRulerDisplayableManager,
            vtkMRMLScalarBarDisplayableManager,
            vtkMRMLSegmentationsDisplayableManager2D,
            vtkMRMLMarkupsDisplayableManager,
            vtkMRMLTransformsDisplayableManager2D,
            vtkMRMLLayerDisplayableManager,
            vtkMRMLLinearTransformsDisplayableManager,
            vtkMRMLColorLegendDisplayableManager,
        ]
        self._initialize_displayable_manager_group(vtkMRMLSliceViewDisplayableManagerFactory, app_logic, managers)
        self.name = name

        # Create slice logic
        self._logic = vtkMRMLSliceLogic()
        self._logic.SetMRMLApplicationLogic(app_logic)
        self._event_observer.UpdateObserver(None, self._logic)
        app_logic.GetSliceLogics().AddItem(self._logic)
        self._interactor_observer.SetSliceLogic(self._logic)
        self._interactor_observer.SetDisplayableManagers(self._displayable_manager_group)

        # Connect to scene
        self.set_scene(scene)
        self.interactor().SetInteractorStyle(vtkInteractorStyleUser())
        self._interactor_observer.SetInteractor(self.interactor())

    def _on_object_event(self, _obj, _event_id, _call_data):
        if _obj == self._logic:
            self._on_slice_logic_modified_event()

        super()._on_object_event(_obj, _event_id, _call_data)

    def _reset_node_view_properties(self):
        super()._reset_node_view_properties()
        if not self._view_node:
            return

        with self.trigger_modified_once():
            self._call_if_value_not_none(self._view_node.SetOrientation, self._view_properties.orientation)
            self._view_node.SetOrientationToDefault()
            self._logic.RotateSliceToLowestVolumeAxes(False)

    def set_scene(self, scene: vtkMRMLScene) -> None:
        super().set_scene(scene)
        self._logic.SetMRMLScene(scene)
        if self._view_node is None:
            self.set_view_node(self._logic.AddSliceNode(self.name))

    def _on_slice_logic_modified_event(self, *_):
        self._update_image_data_connection()

    def _update_image_data_connection(self):
        self._set_image_data_connection(self._logic.GetImageDataConnection())

    def _set_image_data_connection(self, connection):
        if self._image_data_connection == connection:
            return

        self._image_data_connection = connection
        self._render_manager.SetImageDataConnection(self._image_data_connection)

    def _update_slice_size(self, *_):
        self._logic.ResizeSliceNode(*self.render_window().GetSize())

    def set_orientation(
        self,
        orientation: Literal["Coronal", "Sagittal", "Axial"],
    ) -> None:
        self._view_node.SetOrientation(orientation)

    def get_orientation(self) -> str:
        return self._view_node.GetOrientation()

    def fit_view_to_content(self) -> None:
        with self.trigger_modified_once():
            self._update_slice_size()
            self._logic.FitSliceToBackground()
            self._logic.SnapSliceOffsetToIJK()

    def set_background_volume_id(self, volume_id: str | None) -> None:
        self.set_layer_volume_id(SliceLayer.Background, volume_id)

    def get_background_volume_id(self) -> str | None:
        return self.get_layer_volume_id(SliceLayer.Background)

    def set_foreground_volume_id(self, volume_id: str | None) -> None:
        self.set_layer_volume_id(SliceLayer.Foreground, volume_id)

    def get_foreground_volume_id(self) -> str | None:
        return self.get_layer_volume_id(SliceLayer.Foreground)

    def get_slice_range(self) -> tuple[float, float]:
        (range_min, range_max), _ = self._get_slice_range_resolution()
        return range_min, range_max

    def get_slice_step(self) -> float:
        _, resolution = self._get_slice_range_resolution()
        return resolution

    def _get_slice_range_resolution(self) -> tuple[list[float], float]:
        slice_range = [-1.0, -1.0]
        resolution = reference(1.0)

        if not self._logic.GetSliceOffsetRangeResolution(slice_range, resolution):
            return [0, 1], 0.1
        return slice_range, resolution.get()

    def get_slice_value(self) -> float:
        return self._logic.GetSliceOffset()

    def set_slice_value(self, value: float) -> None:
        if value == self.get_slice_value():
            return

        with self.trigger_modified_once():
            self._logic.SetSliceOffset(value)

    def set_visible_in_3d(self, is_visible: bool):
        self._view_node.SetSliceVisible(is_visible)

    def is_visible_in_3d(self) -> bool:
        return self._view_node.GetSliceVisible()

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

        current_fov = self._view_node.GetFieldOfView()
        self._view_node.SetFieldOfView(current_fov[0] * fov_factor, current_fov[1] * fov_factor, current_fov[2])

    def zoom_in(self):
        self.zoom(0.2)

    def zoom_out(self):
        self.zoom(-0.2)

    def set_slab_enabled(self, is_enabled: bool):
        self._view_node.SetSlabReconstructionEnabled(is_enabled)

    def is_slab_enabled(self) -> bool:
        return self._view_node.GetSlabReconstructionEnabled()

    def set_slab_thickness(self, thickness: float):
        self._view_node.SetSlabReconstructionThickness(thickness)

    def get_slab_thickness(self) -> float:
        return self._view_node.GetSlabReconstructionThickness()

    def set_slab_type(
        self,
        slab_type: Literal[
            vtk.VTK_IMAGE_SLAB_SUM, vtk.VTK_IMAGE_SLAB_MAX, vtk.VTK_IMAGE_SLAB_MIN, vtk.VTK_IMAGE_SLAB_MEAN
        ],
    ):
        self._view_node.SetSlabReconstructionType(slab_type)

    def get_slab_type(
        self,
    ) -> Literal[vtk.VTK_IMAGE_SLAB_SUM, vtk.VTK_IMAGE_SLAB_MAX, vtk.VTK_IMAGE_SLAB_MIN, vtk.VTK_IMAGE_SLAB_MEAN]:
        return self._view_node.GetSlabReconstructionType()

    def set_foreground_opacity(self, opacity: float):
        self._logic.GetSliceCompositeNode().SetForegroundOpacity(opacity)
        self.schedule_render()

    def get_foreground_opacity(self) -> float:
        return self._logic.GetSliceCompositeNode().GetForegroundOpacity()

    def set_layer_volume_id(self, layer: int | SliceLayer, volume_id: str | None) -> None:
        setter = (
            self._logic.GetSliceCompositeNode().SetBackgroundVolumeID
            if SliceLayer.as_int(layer) == SliceLayer.Background.value
            else self._logic.GetSliceCompositeNode().SetForegroundVolumeID
        )
        setter(volume_id)
        self.schedule_render()

    def get_layer_volume_id(self, layer: int | SliceLayer) -> str | None:
        getter = (
            self._logic.GetSliceCompositeNode().GetBackgroundVolumeID
            if SliceLayer.as_int(layer) == SliceLayer.Background.value
            else self._logic.GetSliceCompositeNode().GetForegroundVolumeID
        )
        return getter()

    def get_volume_layer_logic(self, volume_node: vtkMRMLVolumeNode) -> vtkMRMLSliceLayerLogic:
        volume_id = volume_node.GetID() if volume_node else ""
        return (
            self._logic.GetForegroundLayer()
            if self.get_foreground_volume_id() == volume_id
            else self._logic.GetBackgroundLayer()
        )
