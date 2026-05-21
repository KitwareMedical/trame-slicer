from __future__ import annotations

from enum import Enum

from slicer import (
    vtkMRMLAbstractViewNode,
    vtkMRMLApplicationLogic,
    vtkMRMLCameraDisplayableManager,
    vtkMRMLCameraNode,
    vtkMRMLColorLegendDisplayableManager,
    vtkMRMLCrosshairDisplayableManager,
    vtkMRMLCrosshairDisplayableManager3D,
    vtkMRMLCrosshairNode,
    vtkMRMLLayerDisplayableManager,
    vtkMRMLLinearTransformsDisplayableManager,
    vtkMRMLMarkupsDisplayableManager,
    vtkMRMLModelDisplayableManager,
    vtkMRMLOrientationMarkerDisplayableManager,
    vtkMRMLRulerDisplayableManager,
    vtkMRMLScene,
    vtkMRMLSegmentationsDisplayableManager3D,
    vtkMRMLThreeDReformatDisplayableManager,
    vtkMRMLThreeDViewDisplayableManagerFactory,
    vtkMRMLThreeDViewInteractorStyle,
    vtkMRMLTransformsDisplayableManager3D,
    vtkMRMLViewDisplayableManager,
    vtkMRMLViewLogic,
    vtkMRMLViewNode,
    vtkMRMLVolumeRenderingDisplayableManager,
)
from vtkmodules.vtkRenderingCore import vtkInteractorStyle3D

from .abstract_view import AbstractView


class RenderView(AbstractView):
    """
    Copied and adapted from ctkVTKRenderView
    """

    def reset_focal_point(self):
        bounds = [0] * 6
        self.renderer().ComputeVisiblePropBounds(bounds)
        x_center = (bounds[1] + bounds[0]) / 2.0
        y_center = (bounds[3] + bounds[2]) / 2.0
        z_center = (bounds[5] + bounds[4]) / 2.0
        self.set_focal_point(x_center, y_center, z_center)

    def set_focal_point(self, x, y, z):
        if not self.renderer().IsActiveCameraCreated():
            return

        camera = self.renderer().GetActiveCamera()
        camera.SetFocalPoint(x, y, z)
        camera.ComputeViewPlaneNormal()
        camera.OrthogonalizeViewUp()
        self.renderer().ResetCameraClippingRange()
        self.renderer().UpdateLightsGeometryToFollowCamera()


class ViewDirection(Enum):
    LEFT = vtkMRMLCameraNode.Left
    RIGHT = vtkMRMLCameraNode.Right
    POSTERIOR = vtkMRMLCameraNode.Posterior
    ANTERIOR = vtkMRMLCameraNode.Anterior
    INFERIOR = vtkMRMLCameraNode.Inferior
    SUPERIOR = vtkMRMLCameraNode.Superior


class ThreeDView(RenderView):
    """
    Copied and adapted from qMRMLThreeDView
    """

    def __init__(
        self,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
        name: str,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.renderer().SetUseDepthPeeling(True)
        self.renderer().SetUseDepthPeelingForVolumes(True)

        managers = [
            vtkMRMLVolumeRenderingDisplayableManager,
            vtkMRMLCameraDisplayableManager,
            vtkMRMLViewDisplayableManager,
            vtkMRMLModelDisplayableManager,
            vtkMRMLThreeDReformatDisplayableManager,
            vtkMRMLCrosshairDisplayableManager3D,
            vtkMRMLOrientationMarkerDisplayableManager,
            vtkMRMLRulerDisplayableManager,
            vtkMRMLSegmentationsDisplayableManager3D,
            vtkMRMLMarkupsDisplayableManager,
            vtkMRMLTransformsDisplayableManager3D,
            vtkMRMLLayerDisplayableManager,
            vtkMRMLLinearTransformsDisplayableManager,
            vtkMRMLColorLegendDisplayableManager,
        ]

        self._initialize_displayable_manager_group(vtkMRMLThreeDViewDisplayableManagerFactory, app_logic, managers)
        self._interactor_observer = vtkMRMLThreeDViewInteractorStyle()
        self._interactor_observer.SetDisplayableManagers(self._displayable_manager_group)
        self._interactor_observer.SetInteractor(self.interactor())
        self.interactor().SetInteractorStyle(vtkInteractorStyle3D())

        self.name = name
        self._logic = vtkMRMLViewLogic()
        self._logic.SetMRMLApplicationLogic(app_logic)

        app_logic.GetViewLogics().AddItem(self._logic)
        self.set_scene(scene)

    def set_scene(self, scene: vtkMRMLScene) -> None:
        super().set_scene(scene)
        self._logic.SetMRMLScene(scene)
        if self._view_node is None:
            self.set_view_node(self._logic.AddViewNode(self.name))

    def reset_focal_point(self):
        saved_box_visible = True
        saved_axis_label_visible = True

        if self._view_node:
            # Save current visibility state of Box and AxisLabel
            saved_box_visible = self._view_node.GetBoxVisible()
            saved_axis_label_visible = self._view_node.GetAxisLabelsVisible()

            was_modifying = self._view_node.StartModify()
            # Hide Box and AxisLabel so they don't get taken into account when computing
            # the view boundaries
            self._view_node.SetBoxVisible(0)
            self._view_node.SetAxisLabelsVisible(0)
            self._view_node.EndModify(was_modifying)

        # Exclude crosshair from focal point computation
        crosshair_node = vtkMRMLCrosshairDisplayableManager().FindCrosshairNode(self._scene)
        crosshairMode = 0
        if crosshair_node:
            crosshairMode = crosshair_node.GetCrosshairMode()
            crosshair_node.SetCrosshairMode(vtkMRMLCrosshairNode.NoCrosshair)

        # Superclass resets the camera.
        super().reset_focal_point()

        if self._view_node:
            # Restore visibility state
            was_modifying = self._view_node.StartModify()
            self._view_node.SetBoxVisible(saved_box_visible)
            self._view_node.SetAxisLabelsVisible(saved_axis_label_visible)
            self._view_node.EndModify(was_modifying)
            # Inform the displayable manager that the view is reset, so it can
            # update the box/labels bounds.
            self._view_node.InvokeEvent(vtkMRMLViewNode.ResetFocalPointRequestedEvent)

        if crosshair_node:
            crosshair_node.SetCrosshairMode(crosshairMode)

        if self.renderer():
            self.renderer().ResetCameraClippingRange()

    def set_background_gradient_color(self, color1_rgb_int, color2_rgb_int):
        super().set_background_gradient_color(color1_rgb_int, color2_rgb_int)
        if not self._view_node:
            return

        self._view_node.SetBackgroundColor(*self._to_float_color(color1_rgb_int))
        self._view_node.SetBackgroundColor2(*self._to_float_color(color2_rgb_int))

    def set_box_visible(self, is_visible):
        if not self._view_node:
            return
        self._view_node.SetBoxVisible(is_visible)
        self._view_node.SetAxisLabelsVisible(is_visible)

    def rotate_to_view_direction(self, view_direction: ViewDirection) -> None:
        camera_node = self.get_camera_node()
        if not camera_node:
            return

        camera_node.RotateTo(view_direction.value)

    def get_camera_node(self) -> vtkMRMLCameraNode | None:
        camera_dm = self._displayable_manager_group.GetDisplayableManagerByClassName("vtkMRMLCameraDisplayableManager")
        if not camera_dm:
            return None
        return camera_dm.GetCameraNode()

    def fit_view_to_content(self):
        with self.trigger_modified_once():
            self.reset_focal_point()
            self.reset_camera()
            self.rotate_to_view_direction(ViewDirection.ANTERIOR)

    def _reset_node_view_properties(self):
        super()._reset_node_view_properties()
        if not self._view_node:
            return

        self._call_if_value_not_none(self.set_box_visible, self._view_properties.box_visible)

    def set_ruler(self, ruler_type: int | None = None, ruler_color: int | None = None):
        if ruler_type and ruler_type != vtkMRMLAbstractViewNode.RulerTypeNone:
            self.set_render_mode_to_orthographic()
        super().set_ruler(ruler_type, ruler_color)

    def set_render_mode_to_orthographic(self):
        self._view_node.SetRenderMode(1)

    def set_render_mode_to_perspective(self):
        self._view_node.SetRenderMode(0)

    def is_render_mode_perspective(self) -> bool:
        return self._view_node.GetRenderMode() == 0

    def zoom(self, factor):
        """
        Move the camera node closer / further from the focal point by a given factor.

        :param factor: Values between -inf and 1. Values greater than 0 will zoom in, below 0 will zoom out
        """
        if self.is_render_mode_perspective():
            self._zoom_camera_position(factor)
        else:
            self._zoom_parallel_scale(factor)

    def _zoom_parallel_scale(self, factor):
        camera_node = self.get_camera_node()

        parallel_factor = 1 - factor
        if parallel_factor <= 0:
            return

        camera_node.SetParallelScale(parallel_factor * camera_node.GetParallelScale())
        camera_node.ResetClippingRange()

    def _zoom_camera_position(self, factor):
        import numpy as np

        if factor >= 1:
            return

        camera_node = self.get_camera_node()
        camera_position = np.array(camera_node.GetPosition())
        focal_point = np.array(camera_node.GetFocalPoint())
        camera_node.SetPosition(camera_position + factor * (focal_point - camera_position))
        camera_node.ResetClippingRange()

    def zoom_in(self):
        self.zoom(0.2)

    def zoom_out(self):
        self.zoom(-0.2)
