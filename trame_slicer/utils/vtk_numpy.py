from __future__ import annotations

import vtkmodules.util.numpy_support as vtk_np
from numpy.typing import NDArray
from vtkmodules.vtkCommonDataModel import vtkImageData
import numpy as np

def vtk_image_to_np(image: vtkImageData) -> NDArray:
    dims = tuple(reversed(image.GetDimensions()))
    scalars = image.GetPointData().GetScalars()
    array = vtk_np.vtk_to_numpy(scalars) if scalars else np.array([])
    return array.reshape(dims)
