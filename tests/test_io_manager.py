from __future__ import annotations

from itertools import chain
from pathlib import Path

import numpy as np
import pytest
from slicer import (
    vtkMRMLModelNode,
    vtkMRMLSegmentationNode,
    vtkMRMLVolumeNode,
    vtkSegmentation,
)
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkIOGeometry import vtkSTLReader

from trame_slicer.core import IOManager, VolumesReader


@pytest.fixture
def an_io_manager(a_slicer_app):
    return IOManager(
        a_slicer_app.scene,
        a_slicer_app.app_logic,
        a_slicer_app.segmentation_editor,
    )


def test_an_io_manager_can_load_a_volume_using_nifti_format(
    an_io_manager,
    a_slicer_app,
    a_nifti_volume_file_path,
):
    volumes = an_io_manager.load_volumes(a_nifti_volume_file_path.as_posix())
    assert volumes
    assert a_slicer_app.scene.GetNodeByID(volumes[0].GetID()) is not None


def test_an_io_manager_can_load_a_volume_using_nrrd_format(
    an_io_manager,
    a_slicer_app,
    a_nrrd_volume_file_path,
):
    volumes = an_io_manager.load_volumes(a_nrrd_volume_file_path.as_posix())
    assert volumes
    assert a_slicer_app.scene.GetNodeByID(volumes[0].GetID()) is not None


def test_an_io_manager_can_load_a_volume_in_dcm_format(
    an_io_manager,
    a_slicer_app,
    mr_head_dcm_volume_file_paths,
):
    volumes = an_io_manager.load_volumes([p.as_posix() for p in mr_head_dcm_volume_file_paths])
    assert volumes
    assert isinstance(volumes[0], vtkMRMLVolumeNode)
    assert a_slicer_app.scene.GetNodeByID(volumes[0].GetID()) is not None


def test_can_split_multiple_dcm_volumes(
    ct_chest_dcm_volume_file_paths,
    mr_head_dcm_volume_file_paths,
):
    volume_files = [p.as_posix() for p in chain(mr_head_dcm_volume_file_paths, ct_chest_dcm_volume_file_paths)]
    split_volumes = VolumesReader.split_volumes(volume_files)
    assert len(split_volumes) == 2


def test_split_volume_returns_original_volume_if_nothing_to_split(
    ct_chest_dcm_volume_file_paths,
):
    volume_files = [p.as_posix() for p in ct_chest_dcm_volume_file_paths]
    split_volumes = VolumesReader.split_volumes(volume_files)
    assert len(split_volumes) == 1
    assert split_volumes == [volume_files]


def test_can_load_multiple_volumes_in_dcm_format(
    an_io_manager,
    ct_chest_dcm_volume_file_paths,
    mr_head_dcm_volume_file_paths,
):
    volume_files = [p.as_posix() for p in chain(mr_head_dcm_volume_file_paths, ct_chest_dcm_volume_file_paths)]

    volumes = an_io_manager.load_volumes(volume_files)
    assert len(volumes) == 2
    assert volumes[0].GetID() != volumes[1].GetID()


def test_an_io_manager_can_load_model_in_stl_format(
    an_io_manager,
    a_model_file_path,
    a_slicer_app,
):
    model = an_io_manager.load_model(a_model_file_path.as_posix())
    assert isinstance(model, vtkMRMLModelNode)
    assert a_slicer_app.scene.GetNodeByID(model.GetID()) is not None


def test_an_io_manager_can_load_segmentations_in_nifti_format(
    an_io_manager,
    a_segmentation_nifti_file_path,
    a_slicer_app,
):
    segmentation_node = an_io_manager.load_segmentation(a_segmentation_nifti_file_path.as_posix())
    assert isinstance(segmentation_node, vtkMRMLSegmentationNode)
    assert a_slicer_app.scene.GetNodeByID(segmentation_node.GetID()) is not None
    segmentation: vtkSegmentation = segmentation_node.GetSegmentation()
    assert segmentation.GetNumberOfSegments() == 1


def test_an_io_manager_can_load_segmentations_in_stl_format(
    an_io_manager,
    a_segmentation_stl_file_path,
    a_slicer_app,
):
    segmentation_node = an_io_manager.load_segmentation(a_segmentation_stl_file_path.as_posix())
    assert isinstance(segmentation_node, vtkMRMLSegmentationNode)
    assert a_slicer_app.scene.GetNodeByID(segmentation_node.GetID()) is not None
    segmentation: vtkSegmentation = segmentation_node.GetSegmentation()
    assert segmentation.GetNumberOfSegments() == 1


def test_an_io_manager_can_write_models(an_io_manager, a_model_node, tmpdir):
    out_path = Path(tmpdir, "out.obj")
    an_io_manager.write_model(a_model_node, out_path)

    src_n_points = a_model_node.GetPolyData().GetNumberOfPoints()
    assert out_path.exists()
    read_model = an_io_manager.load_model(out_path)
    assert read_model.GetPolyData().GetNumberOfPoints() == src_n_points


def test_an_io_manager_can_write_segmentation_as_nifti(an_io_manager, a_segmentation_stl_file_path, tmpdir):
    segmentation_node = an_io_manager.load_segmentation(a_segmentation_stl_file_path.as_posix())
    out_path = Path(tmpdir, "out.nii.gz")
    an_io_manager.write_segmentation(segmentation_node, out_path)
    assert out_path.exists()


def get_np_points(poly: vtkPolyData):
    array = np.zeros((poly.GetNumberOfPoints(), 3))
    vtk_points: vtkPoints = poly.GetPoints()
    for i_pt in range(array.shape[0]):
        array[i_pt, :] = vtk_points.GetPoint(i_pt)
    return array


def read_stl_file_points_as_numpy(stl_file):
    stl_reader = vtkSTLReader()
    stl_reader.SetFileName(Path(stl_file).as_posix())
    stl_reader.Update()
    return get_np_points(stl_reader.GetOutput())


def test_an_io_manager_can_load_save_models_without_changing_their_ref(an_io_manager, a_model_file_path, tmpdir):
    # Load using STL reader
    exp_points = read_stl_file_points_as_numpy(a_model_file_path)

    # Load in slicer with conversion disabled
    model = an_io_manager.load_model(a_model_file_path, do_convert_to_slicer_coord=False)
    model_poly = model.GetPolyData()
    act_points = get_np_points(model_poly)

    # Verify points equal
    np.testing.assert_allclose(act_points, exp_points)

    # Write file to stl and verify written points are as expected
    out_file = Path(tmpdir) / "out.stl"
    an_io_manager.write_model(model, out_file, do_convert_from_slicer_coord=False)

    assert out_file.exists()
    act_points = read_stl_file_points_as_numpy(out_file)
    np.testing.assert_allclose(act_points, exp_points)


def test_an_io_manager_by_default_loads_and_saves_models_as_lps(an_io_manager, a_model_file_path, tmpdir):
    # Load using STL reader
    exp_points = read_stl_file_points_as_numpy(a_model_file_path)

    # Load in slicer with conversion disabled
    model = an_io_manager.load_model(a_model_file_path)
    model_poly = model.GetPolyData()
    act_points = get_np_points(model_poly)

    # Verify points not equal
    with np.testing.assert_raises(AssertionError):
        np.testing.assert_allclose(act_points, exp_points)

    # Write file to stl and verify written points are as source file
    out_file = Path(tmpdir) / "out.stl"
    an_io_manager.write_model(model, out_file)

    assert out_file.exists()
    act_points = read_stl_file_points_as_numpy(out_file)
    np.testing.assert_allclose(act_points, exp_points)


@pytest.mark.parametrize("scene_name", ["scene.mrml", "scene.mrb"])
def test_an_io_manager_can_read_write_scene(an_io_manager, a_slicer_app, scene_name, a_volume_node, tmpdir):
    file_path = Path(tmpdir) / scene_name
    an_io_manager.save_scene(file_path)
    assert file_path.is_file()

    volume_id = a_volume_node.GetID()
    a_slicer_app.scene.Clear()

    an_io_manager.load_scene(file_path)
    assert a_slicer_app.scene.GetNodeByID(volume_id)
