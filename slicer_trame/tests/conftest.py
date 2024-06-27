import itk
import pytest
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkMRMLCore import vtkMRMLVolumeArchetypeStorageNode, vtkMRMLScalarVolumeNode, \
    vtkMRMLScalarVolumeDisplayNode, vtkMRMLColorTableNode, vtkMRMLModelStorageNode, vtkMRMLModelNode

from slicer_trame.app.abstract_view import DirectRendering
from slicer_trame.app.slice_view import SliceView
from slicer_trame.app.slicer_app import SlicerApp
from slicer_trame.app.threed_view import ThreeDView


@pytest.fixture
def a_slicer_app():
    return SlicerApp()


@pytest.fixture
def a_threed_view(a_slicer_app):
    three_d_view = ThreeDView(a_slicer_app, "ThreeD", scheduled_render_strategy=DirectRendering())
    yield three_d_view
    three_d_view.finalize()


@pytest.fixture
def a_slice_view(a_slicer_app):
    return SliceView(a_slicer_app, "Red", scheduled_render_strategy=DirectRendering())


@pytest.fixture
def a_model_node(a_slicer_app):
    return load_model_node(r"C:\Work\Projects\Acandis\POC_SlicerLib_Trame\model.stl", a_slicer_app)


def load_model_node(file_path, a_slicer_app):
    storage_node = vtkMRMLModelStorageNode()
    storage_node.SetFileName(file_path)
    model_node: vtkMRMLModelNode = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode")
    storage_node.ReadData(model_node)
    model_node.CreateDefaultDisplayNodes()
    return model_node


@pytest.fixture
def a_segmentation_model(a_slicer_app):
    return load_model_node(r"C:\Work\Projects\Acandis\POC_SlicerLib_Trame\a_segmentation.stl", a_slicer_app)


@pytest.fixture
def a_volume_node(a_slicer_app):
    storage_node = vtkMRMLVolumeArchetypeStorageNode()
    node = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    storage_node.SetFileName(r"C:\Work\Projects\Acandis\POC_SlicerLib_Trame\MRHead.nrrd")
    storage_node.ReadData(node)
    node.SetAndObserveStorageNodeID(storage_node.GetID())

    return node


@pytest.fixture
def a_volume_node_manually_loaded(a_slicer_app):
    im = itk.imread(r"C:\Work\Projects\Acandis\POC_SlicerLib_Trame\MRHead.nrrd")
    vtk_image = itk.vtk_image_from_image(im)
    node: vtkMRMLScalarVolumeNode = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    node.SetAndObserveImageData(vtk_image)
    node.CreateDefaultDisplayNodes()
    return node


@pytest.fixture
def a_volume_manually_crafted(a_slicer_app):
    import vtk

    displayNode = vtkMRMLScalarVolumeDisplayNode()
    scalarNode = vtkMRMLScalarVolumeNode()

    displayNode.SetAutoWindowLevel(True)
    displayNode.SetInterpolate(False)

    scalarNode.SetName("foo")
    scalarNode.SetScene(a_slicer_app.scene)
    displayNode.SetScene(a_slicer_app.scene)

    imageData = vtk.vtkImageData()
    imageData.SetDimensions(10, 20, 30)
    imageData.AllocateScalars(vtk.VTK_FLOAT, 1)
    imageData.GetPointData().GetScalars().Fill(12.5)

    a_slicer_app.scene.AddNode(displayNode)
    scalarNode.SetAndObserveDisplayNodeID(displayNode.GetID())
    scalarNode.SetAndObserveImageData(imageData)
    a_slicer_app.scene.AddNode(scalarNode)

    colorNode = vtkMRMLColorTableNode()
    colorNode.SetTypeToGrey()
    a_slicer_app.scene.AddNode(colorNode)

    displayNode.SetAndObserveColorNodeID(colorNode.GetID())

    return scalarNode
