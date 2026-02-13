from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkRenderingCore import (
    vtkActor2D,
    vtkPolyDataMapper2D,
    vtkProp,
    vtkProperty2D,
)


class PolygonBrush:
    """Display the draw polygon as 2D lines"""

    def __init__(self):
        super().__init__()
        self._points = vtkPoints()
        self._lines = vtkCellArray()
        self._vertices = vtkCellArray()
        self._poly = vtkPolyData()
        self._poly.SetLines(self._lines)
        self._poly.SetVerts(self._vertices)
        self._poly.SetPoints(self._points)

        self._brush_mapper = vtkPolyDataMapper2D()
        self._brush_mapper.SetInputData(self._poly)
        self._brush_actor = vtkActor2D()
        self._brush_actor.SetMapper(self._brush_mapper)
        self._brush_actor.VisibilityOff()
        props = self._brush_actor.GetProperty()
        props.SetColor(1.0, 1.0, 0.0)
        props.SetPointSize(4.0)
        props.SetLineWidth(2.0)

    def set_visibility(self, visible: bool):
        self._brush_actor.SetVisibility(int(visible))

    def move_last_point(self, x: int, y: int) -> None:
        count = self._points.GetNumberOfPoints()
        if count == 0:
            self.add_point(x, y)
        else:
            self._points.SetPoint(count - 1, [float(x), float(y), 1.0])
            self._points.Modified()

    def add_point(self, x: int, y: int) -> None:
        self._points.InsertNextPoint([float(x), float(y), 1.0])
        count = self._points.GetNumberOfPoints()
        if count > 1:
            self._lines.InsertNextCell(2, [count - 1, count - 2])
        self._vertices.InsertNextCell(1, [count - 1])
        self._points.Modified()

    def reset(self) -> None:
        self._points.SetNumberOfPoints(0)
        self._lines.Reset()
        self._vertices.Reset()
        self._poly.Modified()

    @property
    def points(self) -> vtkPoints:
        return self._points

    def get_prop(self) -> vtkProp:
        """
        Return brush prop.
        Can be used to add or remove the brush from the renderer, configure rendering properties (visibility, color, ...)
        """
        return self._brush_actor

    def get_property(self) -> vtkProperty2D:
        return self._brush_actor.GetProperty()
