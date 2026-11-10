from pathlib import Path

from slicer_core import vtkMRMLColorTableNode

from trame_slicer.core import SlicerApp


def test_initializes_colors_with_share_color_files_content(tmpdir):
    color_folder = Path(tmpdir) / "ColorFiles"
    color_folder.mkdir(parents=True, exist_ok=True)
    my_color_file = color_folder / "my_color_file.txt"
    my_color_file.write_text("0 first_value 255 0 0 255\n1 second_value 0 255 0 0")

    app = SlicerApp(share_directory=tmpdir)
    nodes = list(app.scene.GetNodesByName("my_color_file"))
    assert len(nodes) == 1
    color_node = nodes[0]
    assert isinstance(color_node, vtkMRMLColorTableNode)
    assert color_node.GetNumberOfColors() == 2

    c = [0] * 4
    color_node.GetColor(0, c)
    assert c == [1.0, 0, 0, 1.0]

    color_node.GetColor(1, c)
    assert c == [0, 1.0, 0, 0]
