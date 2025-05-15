from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Literal, get_args

import numpy as np
import pydicom.multival
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from slicer import (
    vtkMRMLApplicationLogic,
    vtkMRMLScene,
    vtkMRMLVolumeArchetypeStorageNode,
    vtkMRMLVolumeNode,
    vtkSlicerVolumesLogic,
)
from vtkmodules.vtkCommonCore import vtkStringArray
from vtkmodules.vtkCommonMisc import vtkErrorCode
from vtkmodules.vtkImagingCore import vtkImageChangeInformation

try:
    from vtkITK import (
        vtkITKArchetypeImageSeriesScalarReader,
        vtkITKArchetypeImageSeriesVectorReaderFile,
        vtkITKArchetypeImageSeriesVectorReaderSeries,
    )
except ImportError:
    from vtkmodules.vtkITK import (
        vtkITKArchetypeImageSeriesScalarReader,
        vtkITKArchetypeImageSeriesVectorReaderFile,
        vtkITKArchetypeImageSeriesVectorReaderSeries,
    )


class _DCMTag:
    sopClassUID = (0x0008, 0x0016)
    photometricInterpretation = (0x0028, 0x0004)
    seriesDescription = (0x0008, 0x103E)
    seriesUID = (0x0020, 0x000E)
    seriesNumber = (0x0020, 0x0011)
    position = (0x0020, 0x0032)
    orientation = (0x0020, 0x0037)
    pixelData = (0x7FE0, 0x0010)
    seriesInstanceUID = (0x0020, 0x000E)
    acquisitionNumber = (0x0020, 0x0012)
    imageType = (0x0008, 0x0008)
    contentTime = (0x0008, 0x0033)
    triggerTime = (0x0018, 0x1060)
    diffusionGradientOrientation = (0x0018, 0x9089)
    imageOrientationPatient = (0x0020, 0x0037)
    numberOfFrames = (0x0028, 0x0008)
    instanceUID = (0x0008, 0x0018)
    windowCenter = (0x0028, 0x1050)
    windowWidth = (0x0028, 0x1051)
    rows = (0x0028, 0x0010)
    columns = (0x0028, 0x0011)


class VolumesReader:
    """
    Adapted from Modules/Scripted/DICOMPlugins/DICOMScalarVolumePlugin.py
    """

    _dcm_io_backend = Literal["GDCM", "DCMTK"]
    dcm_read_lru_cache_size = 5000

    @classmethod
    def load_volumes(
        cls,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
        volume_files: list[str] | str,
    ) -> list[vtkMRMLVolumeNode]:
        if not isinstance(volume_files, list):
            volume_files = [volume_files]

        if len(volume_files) < 1:
            return []

        if cls.contains_dcm_volume(volume_files):
            volume_nodes = cls.load_dcm_volumes(scene, volume_files)
        else:
            volume_nodes = [cls.load_single_file_volume(scene, app_logic, volume_file) for volume_file in volume_files]

        return cls._filter_none(volume_nodes)

    @classmethod
    def load_single_file_volume(
        cls,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
        volume_file: str,
    ) -> vtkMRMLVolumeNode | None:
        file_name, name = cls._file_name_from_volume_path(volume_file)
        file_list = vtkStringArray()
        logic = vtkSlicerVolumesLogic()
        logic.SetMRMLApplicationLogic(app_logic)
        logic.SetMRMLScene(scene)
        options = 0
        return logic.AddArchetypeVolume(file_name, name, options, file_list)

    @classmethod
    def contains_dcm_volume(cls, volume_files: list[str]) -> bool:
        if len(volume_files) < 1:
            return False
        return any(cls.is_dcm_file(volume_file) for volume_file in volume_files)

    @classmethod
    def is_dcm_file(cls, file_name: str) -> bool:
        try:
            dcmread(file_name, stop_before_pixels=True)
            return True
        except InvalidDicomError:
            return False

    @classmethod
    def _is_grayscale(cls, volume_files: list[str]) -> bool:
        if not volume_files:
            return False
        return "MONOCHROME" in cls._dcm_read_tag(volume_files[0], _DCMTag.photometricInterpretation)

    @classmethod
    def _file_name_from_volume_path(cls, volume_files: str) -> tuple[str, str]:
        return volume_files, Path(volume_files).name

    @classmethod
    def load_dcm_volumes(cls, scene: vtkMRMLScene, volume_files: list[vtkMRMLVolumeNode | None]):
        return [cls.load_single_dcm_volume(scene, volume_files) for volume_files in cls.split_volumes(volume_files)]

    @classmethod
    def split_volumes(cls, volume_files: list[str]) -> list[list[str]]:
        if len(volume_files) < 1:
            return []

        # Remove unsupported files
        volume_files = cls._filter_files_without_pixel_values(
            cls._filter_unreadable_dcm_files(cls._filter_dcm_files(volume_files))
        )

        # make sub series volumes based on tag differences
        sub_series_tags = [
            _DCMTag.seriesInstanceUID,
            _DCMTag.acquisitionNumber,
            _DCMTag.imageType,
            _DCMTag.imageOrientationPatient,
            _DCMTag.diffusionGradientOrientation,
        ]

        # Iterate over tags and find every tag values listed in tags and store files associated with tag / value pairs
        sub_series_files = defaultdict(list)
        sub_series_values = defaultdict(list)

        for file in volume_files:
            for tag in sub_series_tags:
                value = cls._dcm_read_tag(file, tag)
                value = cls._closest_value(tag, value, sub_series_values)
                sub_series_files[tag, value].append(file)

        # For each value for which there is more than one value per tag list files
        split_files = set()
        for tag, values in sub_series_values.items():
            if len(values) <= 1:
                continue

            for value in values:
                split_files.add(tuple(sorted(sub_series_files[tag, value])))

        return [list(files) for files in split_files] or [volume_files]

    @classmethod
    def _closest_value(
        cls,
        tag: tuple[int, int],
        value: str,
        sub_series_values: dict[tuple[int, int], list[str]],
    ) -> str:
        vectorTags = {
            _DCMTag.imageOrientationPatient,
            _DCMTag.diffusionGradientOrientation,
        }

        value = value.replace(",", "_")

        if tag not in vectorTags:
            if value not in sub_series_values[tag]:
                sub_series_values[tag].append(value)
            return value

        if not value:
            return value

        vector = cls.tag_value_to_vector(value)
        orientation_epsilon = 1e-6
        for sub_series_value in sub_series_values[tag]:
            sub_series_vector = cls.tag_value_to_vector(sub_series_value)

            if np.allclose(
                vector,
                sub_series_vector,
                rtol=0.0,
                atol=orientation_epsilon,
            ):
                return sub_series_value

        sub_series_values[tag].append(value)
        return value

    @classmethod
    def tag_value_to_vector(cls, value):
        return np.array([float(element) for element in value.split("\\")])

    @classmethod
    def _filter_dcm_files(cls, volume_files: list[str]) -> list[str]:
        return sorted([volume_file for volume_file in volume_files if cls.is_dcm_file(volume_file)])

    @classmethod
    def _filter_files_without_pixel_values(cls, volume_files: list[str]) -> list[str]:
        return [volume_file for volume_file in volume_files if cls._has_pixel_data(volume_file)]

    @classmethod
    def _filter_unreadable_dcm_files(cls, volume_files: list[str]) -> list[str]:
        def unreadable_sop_class(vol_file: str) -> bool:
            sop_uuid = cls._dcm_read_tag(vol_file, _DCMTag.sopClassUID)
            excluded = {"1.2.840.10008.5.1.4.1.1.66.4", "1.2.840.10008.5.1.4.1.1.481.3"}
            return sop_uuid in excluded if sop_uuid is not None else False

        return [volume_file for volume_file in volume_files if not unreadable_sop_class(volume_file)]

    @classmethod
    def _has_pixel_data(cls, volume_file: str) -> bool:
        dcm = dcmread(volume_file)
        return bool(dcm.get(_DCMTag.pixelData))

    @classmethod
    def _filter_none(cls, volume_nodes: list[vtkMRMLVolumeNode | None]) -> list[vtkMRMLVolumeNode]:
        return list(filter(None, volume_nodes))

    @classmethod
    def load_single_dcm_volume(cls, scene: vtkMRMLScene, volume_files: list[str]) -> vtkMRMLVolumeNode | None:
        # Get name and grayscale values
        is_gray_scale = cls._is_grayscale(volume_files)
        name = cls._dcm_series_name(volume_files)

        # Sort files by position
        volume_files = cls._get_sorted_image_files(volume_files)

        for backend in get_args(VolumesReader._dcm_io_backend):
            volume = cls._load_dcm_volume_with_backend(scene, volume_files, name, backend, is_gray_scale)
            if volume is not None:
                return volume
        return None

    @classmethod
    def _dcm_series_name(cls, volume_files: list[str]) -> str:
        """Generate a name suitable for use as a mrml node name based
        on the series level data in the database
        """
        if len(volume_files) < 1:
            return ""
        first_file = volume_files[0]
        series_description = cls._dcm_read_tag(first_file, _DCMTag.seriesDescription)
        series_number = cls._dcm_read_tag(first_file, _DCMTag.seriesNumber)
        name = series_description or "Unnamed Series"
        return f"{series_number}: {name}" if series_number else name

    @classmethod
    def _load_dcm_volume_with_backend(
        cls,
        scene: vtkMRMLScene,
        volume_files: list[str],
        name: str,
        image_io_backend: VolumesReader._dcm_io_backend,
        grayscale=True,
    ):
        if grayscale:
            reader = vtkITKArchetypeImageSeriesScalarReader()
        else:
            reader = (
                vtkITKArchetypeImageSeriesVectorReaderSeries()
                if len(volume_files) > 1
                else vtkITKArchetypeImageSeriesVectorReaderFile()
            )

        reader.SetArchetype(volume_files[0])
        for f in volume_files:
            reader.AddFileName(f)
        reader.SetSingleFile(0)
        reader.SetOutputScalarTypeToNative()
        reader.SetDesiredCoordinateOrientationToNative()
        reader.SetUseNativeOriginOn()
        if image_io_backend == "GDCM":
            reader.SetDICOMImageIOApproachToGDCM()
        elif image_io_backend == "DCMTK":
            reader.SetDICOMImageIOApproachToDCMTK()
        else:
            _error_msg = f"Invalid imageIOName of {image_io_backend}"
            raise Exception(_error_msg)
        reader.Update()

        if reader.GetErrorCode() != vtkErrorCode.NoError:
            error_strings = (
                image_io_backend,
                vtkErrorCode.GetStringFromErrorCode(reader.GetErrorCode()),
            )
            _error_msg = f"Could not read scalar volume using %s approach.  Error is: {error_strings}"
            raise RuntimeError(_error_msg)

        image_change_information = vtkImageChangeInformation()
        image_change_information.SetInputConnection(reader.GetOutputPort())
        image_change_information.SetOutputSpacing(1, 1, 1)
        image_change_information.SetOutputOrigin(0, 0, 0)
        image_change_information.Update()

        name = scene.GenerateUniqueName(name)
        node_type = "vtkMRMLScalarVolumeNode" if grayscale else "vtkMRMLVectorVolumeNode"
        volume_node = scene.AddNewNodeByClass(node_type, name)
        volume_node.SetAndObserveImageData(image_change_information.GetOutputDataObject(0))
        vtkMRMLVolumeArchetypeStorageNode.SetMetaDataDictionaryFromReader(
            volume_node,
            reader,
        )
        volume_node.SetRASToIJKMatrix(reader.GetRasToIjkMatrix())
        volume_node.CreateDefaultDisplayNodes()
        return volume_node

    @classmethod
    def _clean_name(cls, value: str) -> str:
        replace_vals = [
            ("|", "-"),
            ("/", "-"),
            ("\\", "-"),
            ("*", "(star)"),
        ]
        clean_value = value
        for val, rep in replace_vals:
            clean_value = clean_value.replace(val, rep)

        return clean_value

    @classmethod
    @lru_cache(dcm_read_lru_cache_size)
    def _dcm_read_file(cls, dcm_file):
        return dcmread(dcm_file, stop_before_pixels=True)

    @classmethod
    @lru_cache(dcm_read_lru_cache_size)
    def _dcm_read_tag(cls, dcm_file: str, tag) -> str:
        val = cls._dcm_read_file(dcm_file).get(tag)
        if val is None:
            return ""

        val = val.value
        if isinstance(val, pydicom.multival.MultiValue):
            return "\\".join([str(v) for v in val])
        return str(val)

    @classmethod
    def _get_sorted_image_files(cls, volume_files: list[str]) -> list[str]:
        """
        Adapted from : Modules/Scripted/DICOMLib/DICOMUtils.py::DICOMUtils.py

        Sort DICOM image files in increasing slice order (IS direction) corresponding to a series

        Use the first file to get the ImageOrientationPatient for the
        series and calculate the scan direction (assumed to be perpendicular
        to the acquisition plane)
        """

        if not volume_files:
            return []

        # Make sure first file contains valid geometry
        ref_orientation = cls._dcm_read_tag(volume_files[0], _DCMTag.orientation)
        ref_position = cls._dcm_read_tag(volume_files[0], _DCMTag.position)
        if not all([ref_orientation, ref_position]):
            return volume_files

        # Determine out-of-plane direction for first slice
        slice_axes = [float(zz) for zz in ref_orientation.split("\\")]
        ref_x = np.array(slice_axes[:3])
        ref_y = np.array(slice_axes[3:])
        scan_axis = np.cross(ref_x, ref_y)
        scan_origin = np.array([float(zz) for zz in ref_position.split("\\")])

        # For each file in series, calculate the distance along the scan axis, sort files by this
        sort_list = []
        for file in volume_files:
            position_str = cls._dcm_read_tag(file, _DCMTag.position)
            orientation_str = cls._dcm_read_tag(file, _DCMTag.orientation)
            if not position_str or not orientation_str:
                return volume_files

            position = np.array([float(zz) for zz in position_str.split("\\")])
            vec = position - scan_origin
            dist = vec.dot(scan_axis)
            sort_list.append((file, dist))

        return [file for file, dist in sorted(sort_list, key=lambda x: x[1])]
