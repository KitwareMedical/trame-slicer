from __future__ import annotations

import math

from vtkmodules.vtkCommonCore import reference as vtk_ref

from trame_slicer.views.threed_view import ThreeDView

from .brush_model import BrushModel, BrushShape
from .segmentation_paint_widget import SegmentationPaintWidget


class SegmentationPaintWidget3D(SegmentationPaintWidget):
    def __init__(self, view: ThreeDView):
        super().__init__(BrushModel(BrushShape.Sphere))
        self._view = view
        self._last_position: tuple[float, float, float] | None = None

    def absolute_brush_diameter(self) -> float:
        screenSizePixel = self._view.render_window().GetScreenSize()[1]
        # Viewport: xmin, ymin, xmax, ymax; range: 0.0-1.0; origin is bottom left
        # Determine the available renderer size in pixels
        minX = vtk_ref(0.0)
        minY = vtk_ref(0.0)
        self._view.renderer().NormalizedDisplayToDisplay(minX, minY)
        maxX = vtk_ref(1.0)
        maxY = vtk_ref(1.0)
        self._view.renderer().NormalizedDisplayToDisplay(maxX, maxY)
        rendererSizeInPixels = (
            int(maxX.get() - minX.get()),
            int(maxY.get() - minY.get()),
        )
        cam = self._view.renderer().GetActiveCamera()
        if cam.GetParallelProjection():
            # Parallel scale: height of the viewport in world-coordinate distances.
            # Larger numbers produce smaller images.
            mmPerPixel = (cam.GetParallelScale() * 2.0) / float(rendererSizeInPixels[1])
        else:
            tmp = cam.GetFocalPoint()
            cameraFP = (tmp[0], tmp[1], tmp[2], 1.0)
            cameraViewUp = cam.GetViewUp()

            # Get distance in pixels between two points at unit distance above and below the focal point
            self._view.renderer().SetWorldPoint(
                cameraFP[0] + cameraViewUp[0],
                cameraFP[1] + cameraViewUp[1],
                cameraFP[2] + cameraViewUp[2],
                cameraFP[3],
            )
            self._view.renderer().WorldToDisplay()
            topCenter = self._view.renderer().GetDisplayPoint()
            self._view.renderer().SetWorldPoint(
                cameraFP[0] - cameraViewUp[0],
                cameraFP[1] - cameraViewUp[1],
                cameraFP[2] - cameraViewUp[2],
                cameraFP[3],
            )
            self._view.renderer().WorldToDisplay()
            bottomCenter = self._view.renderer().GetDisplayPoint()
            distInPixels = math.dist(topCenter, bottomCenter)

            # 2.0 = 2x length of viewUp vector in mm (because viewUp is unit vector)
            mmPerPixel = 2.0 / distInPixels

        brushRelativeDiameter = 3.0
        return screenSizePixel * (brushRelativeDiameter / 100.0) * mmPerPixel

    def invalidate_last_position(self) -> None:
        self._last_position = None

    def update_widget_position(self, position: list[float]) -> None:
        if self.is_painting():
            if self._last_position:
                self._interpolated_brush_position_if_needed(position)

            self.add_point_to_selection(position)

        self._brush_model.set_shape(BrushShape.Sphere)
        self._brush_model.world_origin_to_world_transform.Identity()
        self._brush_model.world_origin_to_world_transform.Translate(position)
        self._last_position = position

    def _interpolated_brush_position_if_needed(self, position):
        assert self._last_position is not None

        stroke_length = math.dist(position, self._last_position)
        maximum_distance_between_points = 0.2 * self.absolute_brush_diameter()
        if maximum_distance_between_points <= 0.0:
            return

        n_points_to_add = int(stroke_length / maximum_distance_between_points) - 1
        for i_pt in range(n_points_to_add):
            weight = float(i_pt + 1) / float(n_points_to_add + 1)

            weighted_point = [weight * self._last_position[i] + (1.0 - weight) * position[i] for i in range(3)]
            self.add_point_to_selection(weighted_point)
