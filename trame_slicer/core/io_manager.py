from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from slicer import (
    vtkDataIOManagerLogic,
    vtkMRMLApplicationLogic,
    vtkMRMLModelNode,
    vtkMRMLModelStorageNode,
    vtkMRMLRemoteIOLogic,
    vtkMRMLScene,
    vtkMRMLSegmentationNode,
    vtkMRMLStorageNode,
    vtkMRMLVolumeNode,
)

from .segmentation_editor import SegmentationEditor
from .volumes_reader import VolumesReader


class IOManager:
    """
    Class responsible for loading files in the scene.
    """

    def __init__(
        self,
        scene: vtkMRMLScene,
        app_logic: vtkMRMLApplicationLogic,
        segmentation_editor: SegmentationEditor,
    ):
        self.scene = scene
        self.app_logic = app_logic

        # Configure IO logic to enable loading from MRB format
        self.cache_dir = TemporaryDirectory()

        self.remote_io = vtkMRMLRemoteIOLogic()
        self.remote_io.SetMRMLScene(self.scene)
        self.remote_io.SetMRMLApplicationLogic(self.app_logic)
        self.remote_io.GetCacheManager().SetRemoteCacheDirectory(self.cache_dir.name)

        self.vtk_io_manager_logic = vtkDataIOManagerLogic()
        self.vtk_io_manager_logic.SetMRMLScene(scene)
        self.vtk_io_manager_logic.SetMRMLApplicationLogic(app_logic)
        self.vtk_io_manager_logic.SetAndObserveDataIOManager(self.remote_io.GetDataIOManager())
        self.remote_io.AddDataIOToScene()

        self.segmentation_editor: SegmentationEditor = segmentation_editor

    def load_volumes(
        self,
        volume_files: str | list[str],
    ) -> list[vtkMRMLVolumeNode]:
        return VolumesReader.load_volumes(self.scene, self.app_logic, volume_files)

    def load_model(
        self,
        model_file: str | Path,
        do_convert_to_slicer_coord: bool = True,
    ) -> vtkMRMLModelNode | None:
        model_file = Path(model_file).resolve()
        if not model_file.is_file():
            return None

        storage_node = vtkMRMLModelStorageNode()
        storage_node.SetFileName(model_file.as_posix())
        model_name = model_file.stem
        model_node: vtkMRMLModelNode = self.scene.AddNewNodeByClass("vtkMRMLModelNode", model_name)
        storage_node.ReadData(model_node)

        # Check if RAS / LPS conversion is required
        # Slicer will read coordinates in the file header during load regarding of preferred load format
        # Check if coordinate change occurred to rollback change if requested
        did_convert_coord = storage_node.GetCoordinateSystem() != vtkMRMLStorageNode.CoordinateSystemRAS
        if not do_convert_to_slicer_coord and did_convert_coord:
            storage_node.ConvertBetweenRASAndLPS(model_node.GetPolyData(), model_node.GetPolyData())

        model_node.CreateDefaultDisplayNodes()
        return model_node

    @classmethod
    def write_model(
        cls,
        model_node,
        model_file: str | Path,
        do_convert_from_slicer_coord: bool = True,
    ) -> None:
        cls.write_node(
            model_node,
            model_file,
            vtkMRMLModelStorageNode,
            do_convert_from_slicer_coord,
        )

    def load_segmentation(
        self, segmentation_file: str | Path, do_convert_to_slicer_coord=True
    ) -> vtkMRMLSegmentationNode | None:
        if Path(segmentation_file).suffix in [".obj", ".stl", ".ply"]:
            model = self.load_model(segmentation_file, do_convert_to_slicer_coord)
            try:
                return self.segmentation_editor.create_segmentation_node_from_model_node(model)
            finally:
                self.scene.RemoveNode(model)

        return self.segmentation_editor.load_segmentation_from_file(segmentation_file)

    def write_segmentation(self, segmentation_node, segmentation_file: str | Path):
        self.segmentation_editor.export_segmentation_to_file(segmentation_node, segmentation_file)

    @classmethod
    def write_node(
        cls,
        node,
        node_file,
        storage_type: type,
        do_convert_from_slicer_coord: bool,
    ) -> None:
        if not node:
            return

        node_file = Path(node_file).resolve().as_posix()
        storage_node = storage_type()

        if hasattr(storage_node, "SetCoordinateSystem"):
            storage_node.SetCoordinateSystem(
                vtkMRMLStorageNode.CoordinateSystemLPS
                if do_convert_from_slicer_coord
                else vtkMRMLStorageNode.CoordinateSystemRAS
            )
        storage_node.SetFileName(node_file)
        storage_node.WriteData(node)

    def load_scene(self, scene_path) -> bool:
        scene_path = Path(scene_path)
        if not scene_path.is_file():
            return False

        if scene_path.name.endswith("mrb"):
            return self._load_mrb_scene(scene_path)
        return self._load_mrml_scene(scene_path)

    def save_scene(self, scene_path: str | Path) -> bool:
        scene_path = Path(scene_path)
        scene_path = scene_path.resolve()
        base_dir = scene_path.parent
        base_dir.mkdir(parents=True, exist_ok=True)
        self.scene.SetURL(scene_path.as_posix())
        self.scene.SetRootDirectory(base_dir.as_posix())

        if scene_path.name.endswith(".mrml"):
            return self.scene.Commit()
        return self.scene.WriteToMRB(scene_path.as_posix())

    def _load_mrml_scene(self, scene_path: Path) -> bool:
        if not scene_path.is_file():
            return False
        self.scene.SetURL(scene_path.as_posix())
        return self.scene.Import(None)

    def _load_mrb_scene(self, scene_path: Path) -> bool:
        try:
            with TemporaryDirectory() as tmpdir, ZipFile(scene_path, "r") as zip_file:
                zip_file.extractall(tmpdir)
                return self._load_mrml_scene(next(Path(tmpdir).rglob("*.mrml")))
        except StopIteration:
            return False
