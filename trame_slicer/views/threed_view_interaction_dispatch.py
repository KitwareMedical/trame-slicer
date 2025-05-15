from __future__ import annotations

from typing import TYPE_CHECKING

from slicer import vtkMRMLInteractionEventData
from vtkmodules.vtkCommonCore import vtkCommand, vtkMath, vtkPoints
from vtkmodules.vtkRenderingCore import (
    vtkAbstractPropPicker,
    vtkActor,
    vtkCamera,
    vtkHardwarePicker,
    vtkRenderer,
)
from vtkmodules.vtkRenderingVolume import vtkVolumePicker

if TYPE_CHECKING:
    from .threed_view import ThreeDView


from .view_interaction_dispatch import ViewInteractionDispatch


class ThreedViewInteractionDispatch(ViewInteractionDispatch):
    def __init__(self, view: ThreeDView):
        super().__init__(view)

        # Use hardware picker in through vtkWorldPointPicker, this may be slightly slower
        # for generic cases, but way more efficient for some use cases (e.g. segmentation widget)
        # since we won't have to pick multiple times.
        self._volume_picker = vtkVolumePicker()
        self._volume_picker.SetPickFromList(True)  # will only pick volumes

        self._actors_picker = vtkHardwarePicker()
        self._actors_picker.SetPickFromList(True)

        self._last_world_position = [0.0, 0.0, 0.0]
        self._last_pick_hit = None

    def process_event_data(self, event_data: vtkMRMLInteractionEventData):
        super().process_event_data(event_data)
        if event_data.GetType() == vtkCommand.MouseMoveEvent:
            position = self._view.interactor().GetEventPosition()
            hit, world_position = self._quick_pick(position, event_data.GetRenderer())
            self._last_pick_hit = hit
            self._last_world_position = world_position

        # set "inaccurate" world position
        event_data.SetWorldPosition(self._last_world_position, False)

    def has_pick_hit(self) -> bool:
        return bool(self._last_pick_hit)

    def _quick_pick(
        self, display_position: tuple[int, int], poked_renderer: vtkRenderer
    ) -> tuple[bool, tuple[float, float, float]] | None:
        camera_node = self._view.get_camera_node()
        no_pick = False, [0, 0, 0]
        if camera_node is None:
            return no_pick

        # Pick at display position with actor and volume picker
        self._pick(self._volume_picker, display_position, poked_renderer, True)
        self._pick(self._actors_picker, display_position, poked_renderer, False)

        # Filter the closest position to the camera as the latest world position value
        position = self._closest_pick_position_to_camera(
            self._get_picked_positions(),
            camera_node.GetCamera(),
        )
        if position is not None:
            return True, position
        return no_pick

    def _get_picked_positions(self):
        positions = self._volume_picker.GetPickedPositions()
        if self._actors_picker.GetActor():
            positions.InsertNextPoint(self._actors_picker.GetPickPosition())
        return positions

    @staticmethod
    def _pick(
        picker: vtkAbstractPropPicker,
        display_position: tuple[int, int],
        poked_renderer: vtkRenderer,
        is_volume: bool,
    ) -> None:
        """
        Handles the process of picking objects from a scene based on a display position.
        The method filters the objects in the renderer's view according to their type
        and instructs the picker to identify picked objects. Supports both volume picking
        and actor picking modes and clears any prior pick list before execution.

        :param picker: An instance of vtkAbstractPropPicker responsible for picking
            objects in the render window.
        :param display_position: A tuple representing the x, y, position in display coordinates
            where the picker will pick.
        :param poked_renderer: An instance of vtkRenderer representing the renderer
            containing the props to be picked.
        :param is_volume: A boolean indicating whether the picking process is focusing on
            volumes (if True) or actors (if False).
        :return: None
        """
        pick_list = picker.GetPickList()
        pick_list.RemoveAllItems()

        props = poked_renderer.GetViewProps()
        props.InitTraversal()
        prop = props.GetNextProp()
        while prop is not None:
            if is_volume:
                prop.GetVolumes(pick_list)
            elif isinstance(prop, vtkActor):
                prop.GetActors(pick_list)
            prop = props.GetNextProp()

        picker.Pick(display_position[0], display_position[1], 0, poked_renderer)

    @staticmethod
    def _closest_pick_position_to_camera(picked_positions: vtkPoints, camera: vtkCamera) -> list[float] | None:
        """
        Finds the closest picked position to the camera.

        This method computes the closest position among the provided `picked_positions` to the
        position of the given `camera`. The distance is calculated using the square of the
        Euclidean distance between points. If there are no picked positions, the method
        returns `None`.

        :param picked_positions: A `vtkPoints` instance containing the positions to be
            evaluated for closeness to the camera.
        :param camera: A `vtkCamera` object whose position is used as a reference to
            compute the closest point.
        :return: The closest position to the camera as a tuple of coordinates. Returns
            `None` if no positions are provided.
        """
        n_pts = picked_positions.GetNumberOfPoints()
        if n_pts < 1:
            return None

        camera_pos = camera.GetPosition()
        closest_pos = picked_positions.GetPoint(0)
        min_dist = vtkMath.Distance2BetweenPoints(closest_pos, camera_pos)
        for i_pt in range(1, n_pts):
            pos = picked_positions.GetPoint(i_pt)
            dist = vtkMath.Distance2BetweenPoints(pos, camera_pos)
            if dist < min_dist:
                min_dist, closest_pos = dist, pos

        return closest_pos
