from __future__ import annotations

from enum import Enum, auto

from slicer import (
    vtkOrientedImageData,
    vtkOrientedImageDataResample,
)
from vtkmodules.vtkCommonCore import VTK_UNSIGNED_CHAR, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPolyData
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkFiltersCore import vtkThreshold, vtkWindowedSincPolyDataFilter
from vtkmodules.vtkFiltersGeneral import vtkDiscreteMarchingCubes
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkImagingCore import vtkImageChangeInformation, vtkImageThreshold
from vtkmodules.vtkImagingGeneral import vtkImageGaussianSmooth, vtkImageMedian3D
from vtkmodules.vtkImagingMorphological import vtkImageOpenClose3D
from vtkmodules.vtkImagingStencil import vtkImageStencil, vtkPolyDataToImageStencil

from .abstract_segmentation_effect_brush import AbstractSegmentationEffectBrush
from .segment_modifier import ModificationMode


class SmoothingEffectMode(Enum):
    MEDIAN = auto()
    OPENING = auto()
    CLOSING = auto()
    GAUSSIAN = auto()
    JOINT = auto()


class SegmentationEffectSmoothing(AbstractSegmentationEffectBrush):
    def __init__(self) -> None:
        super().__init__(ModificationMode.Set)
        self.smoothing_mode: SmoothingEffectMode = SmoothingEffectMode.MEDIAN
        self.kernel_size: float = 0  # Used for MEDIAN, OPENING and CLOSING smoothing methods
        self.standard_deviation: float = 0  # Used for GAUSSIAN smoothing method
        self.joint_smoothing_factor: float = 0.5  # Used for JOINT smoothing method

    def set_smoothing_mode(self, mode: SmoothingEffectMode):
        self.smoothing_mode = mode

    def set_kernel_size(self, kernel_size: float):
        self.kernel_size = kernel_size

    def set_standard_deviation(self, standard_deviation: float):
        self.standard_deviation = standard_deviation

    def set_joint_smoothing_factor(self, joint_smoothing_factor: float):
        self.joint_smoothing_factor = joint_smoothing_factor

    @staticmethod
    def _get_kernel_size_px(kernel_size_mm: float, labelmap: vtkImageData) -> tuple[float, float, float]:
        spacing = labelmap.GetSpacing()
        return [
            max(1, int(round((kernel_size_mm / spacing[i] + 1) / 2) * 2 - 1))  # Nearest odd number with a minimum of 1
            for i in range(3)
        ]

    @staticmethod
    def _to_oriented_image_data(
        image_data: vtkImageData, reference_labelmap: vtkOrientedImageData
    ) -> vtkOrientedImageData:
        oriented_image = vtkOrientedImageData()
        oriented_image.ShallowCopy(image_data)
        oriented_image.CopyDirections(reference_labelmap)
        return oriented_image

    @staticmethod
    def _get_binary_labelmap(labelmap: vtkImageData, in_value: int, out_value: int):
        threshold_filter = vtkImageThreshold()
        threshold_filter.SetInputData(labelmap)
        threshold_filter.ThresholdByLower(0)
        threshold_filter.SetInValue(out_value)  # Image <= 0
        threshold_filter.SetOutValue(in_value)
        threshold_filter.SetOutputScalarType(labelmap.GetScalarType())
        threshold_filter.Update()
        return threshold_filter.GetOutput()

    def _mask_labelmap(
        self,
        masked_labelmap: vtkOrientedImageData,
        cutout_labelmap: vtkOrientedImageData,
        mask_labelmap: vtkOrientedImageData,
    ) -> vtkOrientedImageData:
        """
        Return output of masked_labelmap & mask_labelmap + cutout_labelmap & NOT(mask_labelmap)
        """
        masked_source = vtkOrientedImageData()
        masked_source.DeepCopy(masked_labelmap)
        vtkOrientedImageDataResample.ApplyImageMask(masked_source, mask_labelmap, 0.0, False)

        masked_cutout = vtkOrientedImageData()
        masked_cutout.DeepCopy(cutout_labelmap)
        vtkOrientedImageDataResample.ApplyImageMask(masked_cutout, mask_labelmap, 0.0, True)

        output_image = vtkOrientedImageData()
        vtkOrientedImageDataResample.MergeImage(
            masked_source,
            masked_cutout,
            output_image,
            vtkOrientedImageDataResample.OPERATION_MAXIMUM,
        )
        return output_image

    def _apply_change(self, modifier_labelmap: vtkOrientedImageData, mask_labelmap: vtkOrientedImageData | None = None):
        if mask_labelmap is not None:
            segment_labelmap = self.modifier.get_segment_labelmap(self.modifier.active_segment_id)
            modifier_labelmap = self._mask_labelmap(modifier_labelmap, segment_labelmap, mask_labelmap)

        self.modifier.apply_labelmap(modifier_labelmap)

    def apply_median_smoothing(
        self,
        kernel_size: float,
        segment_id: str,
        mask_labelmap: vtkOrientedImageData | None = None,
    ):
        segment_labelmap = self.modifier.get_segment_labelmap(segment_id)
        smoothing_filter = vtkImageMedian3D()
        smoothing_filter.SetInputData(segment_labelmap)
        smoothing_filter.SetKernelSize(*self._get_kernel_size_px(kernel_size, segment_labelmap))
        smoothing_filter.Update()
        modifier_labelmap = self._to_oriented_image_data(smoothing_filter.GetOutput(), segment_labelmap)

        self._apply_change(modifier_labelmap, mask_labelmap)

    def _apply_morphological_operator(
        self,
        kernel_size: float,
        segment_id: str,
        mask_labelmap: vtkOrientedImageData | None = None,
        *,
        morph_open: bool,
    ):
        segment_labelmap = self.modifier.get_segment_labelmap(segment_id)

        label_value = 1
        background_value = 0
        binary_labelmap = self._get_binary_labelmap(segment_labelmap, label_value, background_value)

        open_value = label_value if morph_open else background_value
        close_value = background_value if morph_open else label_value
        smoothing_filter = vtkImageOpenClose3D()
        smoothing_filter.SetInputData(binary_labelmap)
        smoothing_filter.SetOpenValue(open_value)
        smoothing_filter.SetCloseValue(close_value)
        smoothing_filter.SetKernelSize(*self._get_kernel_size_px(kernel_size, segment_labelmap))
        smoothing_filter.Update()
        modifier_labelmap = self._to_oriented_image_data(smoothing_filter.GetOutput(), segment_labelmap)

        self._apply_change(modifier_labelmap, mask_labelmap)

    def apply_opening(
        self,
        kernel_size: float,
        segment_id: str,
        mask_labelmap: vtkOrientedImageData | None = None,
    ):
        self._apply_morphological_operator(kernel_size, segment_id, mask_labelmap, morph_open=True)

    def apply_closing(
        self,
        kernel_size: float,
        segment_id: str,
        mask_labelmap: vtkOrientedImageData | None = None,
    ):
        self._apply_morphological_operator(kernel_size, segment_id, mask_labelmap, morph_open=False)

    def apply_gaussian_smoothing(
        self,
        std: float,
        segment_id: str,
        mask_labelmap: vtkOrientedImageData | None = None,
    ):
        segment_labelmap = self.modifier.get_segment_labelmap(segment_id)
        max_value = 255
        radius_factor = 4.0  # Magic number from 3DSlicer's codebase
        std_px = [std / spacing for spacing in segment_labelmap.GetSpacing()]

        # Apply gaussian blur on binarized labelmap
        binary_labelmap = self._get_binary_labelmap(segment_labelmap, segment_labelmap.GetScalarTypeMax(), 0)
        gaussian_filter = vtkImageGaussianSmooth()
        gaussian_filter.SetInputData(binary_labelmap)
        gaussian_filter.SetStandardDeviation(*std_px)
        gaussian_filter.SetRadiusFactor(radius_factor)
        gaussian_filter.Update()

        # Threshold blurred binarized labelmap at half the positive value of the binarization
        threshold_filter = vtkImageThreshold()
        threshold_filter.SetInputConnection(gaussian_filter.GetOutputPort())
        threshold_filter.ThresholdByUpper(int(max_value / 2))
        threshold_filter.SetInValue(1)
        threshold_filter.SetOutValue(0)
        threshold_filter.SetOutputScalarType(segment_labelmap.GetScalarType())
        threshold_filter.Update()
        modifier_labelmap = self._to_oriented_image_data(threshold_filter.GetOutput(), segment_labelmap)

        self._apply_change(modifier_labelmap, mask_labelmap)

    def apply_joint_smoothing(self, smoothing_factor: float, mask_labelmap: vtkOrientedImageData | None = None):
        # This function is majoritarily a reimplementation of SegmentEditorSmoothingEffect.smoothMultipleSegments from
        # the 3D Slicer source code, with minor modifications to fit trame-slicer's codestyle better
        # To keep behavior coherent with 3D Slicer Desktop, this method should be updated if and only if the source function has been
        if smoothing_factor <= 0 or smoothing_factor > 1:
            return

        visible_segment_ids = self.modifier.segmentation.get_visible_segment_ids()
        if len(visible_segment_ids) == 0:
            return

        # Generate merged labelmap of all visible segments
        merged_image = self.modifier.segmentation.get_merged_segment_labelmap(only_visible_segments=True)
        if merged_image is None:
            return

        segment_label_values = {segment_id: i + 1 for i, segment_id in enumerate(visible_segment_ids)}

        # Perform smoothing in voxel space
        spacing = (1, 1, 1)
        origin = (0, 0, 0)
        ici = vtkImageChangeInformation()
        ici.SetInputData(merged_image)
        ici.SetOutputSpacing(*spacing)
        ici.SetOutputOrigin(*origin)

        # Convert labelmap to combined polydata
        # vtkDiscreteFlyingEdges3D cannot be used here, as in the output of that filter,
        # each labeled region is completely disconnected from neighboring regions, and
        # for joint smoothing it is essential for the points to move together.
        convert_to_polydata = vtkDiscreteMarchingCubes()
        convert_to_polydata.SetInputConnection(ici.GetOutputPort())
        convert_to_polydata.SetNumberOfContours(len(segment_label_values))

        for i, label_value in enumerate(segment_label_values.values()):
            convert_to_polydata.SetValue(i, label_value)

        # Low-pass filtering using Taubin's method
        smoothing_iterations = 100  # according to VTK documentation 10-20 iterations could be enough but we use a higher value to reduce chance of shrinking
        pass_band = pow(10.0, -4.0 * smoothing_factor)  # gives a nice range of 1-0.0001 from a user input of 0-1
        smoother = vtkWindowedSincPolyDataFilter()
        smoother.SetInputConnection(convert_to_polydata.GetOutputPort())
        smoother.SetNumberOfIterations(smoothing_iterations)
        smoother.BoundarySmoothingOff()
        smoother.FeatureEdgeSmoothingOff()
        smoother.SetFeatureAngle(90.0)
        smoother.SetPassBand(pass_band)
        smoother.NonManifoldSmoothingOn()
        smoother.NormalizeCoordinatesOn()

        # Extract a label
        threshold = vtkThreshold()
        threshold.SetInputConnection(smoother.GetOutputPort())

        # Convert to polydata
        geometry_filter = vtkGeometryFilter()
        geometry_filter.SetInputConnection(threshold.GetOutputPort())

        # Convert polydata to stencil
        polydata_image_to_stencil = vtkPolyDataToImageStencil()
        polydata_image_to_stencil.SetInputConnection(geometry_filter.GetOutputPort())
        polydata_image_to_stencil.SetOutputSpacing(*spacing)
        polydata_image_to_stencil.SetOutputOrigin(*origin)
        polydata_image_to_stencil.SetOutputWholeExtent(merged_image.GetExtent())

        # Convert stencil to image
        stencil = vtkImageStencil()
        empty_binary_labelmap = vtkImageData()
        empty_binary_labelmap.SetExtent(merged_image.GetExtent())
        empty_binary_labelmap.AllocateScalars(VTK_UNSIGNED_CHAR, 1)
        vtkOrientedImageDataResample.FillImage(empty_binary_labelmap, 0)
        stencil.SetInputData(empty_binary_labelmap)
        stencil.SetStencilConnection(polydata_image_to_stencil.GetOutputPort())
        stencil.ReverseStencilOn()
        stencil.SetBackgroundValue(1)  # General foreground value is 1 (background value because of reverse stencil)

        image_to_world_matrix = vtkMatrix4x4()
        merged_image.GetImageToWorldMatrix(image_to_world_matrix)

        with self.modifier.group_undo_commands(f"Joint segmentation of {','.join(segment_label_values.keys())}"):
            for label_value in segment_label_values.values():
                threshold.SetLowerThreshold(label_value)
                threshold.SetUpperThreshold(label_value)
                threshold.SetThresholdFunction(vtkThreshold.THRESHOLD_BETWEEN)
                stencil.Update()
                smoothed_binary_labelmap = vtkOrientedImageData()
                smoothed_binary_labelmap.ShallowCopy(stencil.GetOutput())
                smoothed_binary_labelmap.SetImageToWorldMatrix(image_to_world_matrix)
                self._apply_change(smoothed_binary_labelmap, mask_labelmap)

    def apply_smoothing(
        self,
        mask_labelmap: vtkOrientedImageData | None = None,
        smoothing_mode: SmoothingEffectMode | None = None,
    ):
        smoothing_mode = smoothing_mode or self.smoothing_mode
        match smoothing_mode.value:
            case SmoothingEffectMode.MEDIAN.value:
                self.apply_median_smoothing(self.kernel_size, self.modifier.active_segment_id, mask_labelmap)
            case SmoothingEffectMode.OPENING.value:
                self.apply_opening(self.kernel_size, self.modifier.active_segment_id, mask_labelmap)
            case SmoothingEffectMode.CLOSING.value:
                self.apply_closing(self.kernel_size, self.modifier.active_segment_id, mask_labelmap)
            case SmoothingEffectMode.GAUSSIAN.value:
                self.apply_gaussian_smoothing(self.standard_deviation, self.modifier.active_segment_id, mask_labelmap)
            case SmoothingEffectMode.JOINT.value:
                self.apply_joint_smoothing(self.joint_smoothing_factor, mask_labelmap)
            case _:
                error_msg = f"Unrecognized smoothing mode: {smoothing_mode}"
                raise ValueError(error_msg)

    def paint_glyph_at_world_coordinates(self, polydata: vtkPolyData, paint_coordinates_world: vtkPoints):
        mask_labelmap = self.modifier.create_modifier_labelmap()
        self.modifier.paint_glyph_in_labelmap(polydata, paint_coordinates_world, mask_labelmap)
        self.apply_smoothing(mask_labelmap)
