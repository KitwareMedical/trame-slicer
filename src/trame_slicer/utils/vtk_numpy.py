from __future__ import annotations

import vtkmodules.util.numpy_support as vtk_np
from numpy.typing import NDArray
from vtkmodules.vtkCommonDataModel import vtkImageData


def vtk_image_to_np(image: vtkImageData) -> NDArray:
    dims = tuple(reversed(image.GetDimensions()))
    return vtk_np.vtk_to_numpy(image.GetPointData().GetScalars()).reshape(dims)
