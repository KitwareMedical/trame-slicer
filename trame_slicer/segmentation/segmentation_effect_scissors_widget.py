from slicer import vtkMRMLInteractionEventData

from .segmentation_polygon_widget import SegmentationPolygonPipeline


class SegmentationScissorsPipeline(SegmentationPolygonPipeline):
    def _LeftButtonPressed(self, event_data: vtkMRMLInteractionEventData) -> bool:
        x, y = event_data.GetDisplayPosition()
        self.widget.start_painting(x, y)
        self.RequestRender()
        return True

    def _LeftButtonReleased(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        self.widget.stop_painting()
        self.RequestRender()
        return True

    def _MouseMoved(self, event_data: vtkMRMLInteractionEventData) -> bool:
        x, y = event_data.GetDisplayPosition()
        self.widget.move_last_point(x, y)
        if self.widget.is_painting():
            self.widget.add_point(x, y)
        self.RequestRender()

        # Always let other interactor and displayable managers do whatever they want
        return False

    def _RightButtonPressed(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        return True

    def _RightButtonReleased(self, _event_data: vtkMRMLInteractionEventData) -> bool:
        return True
