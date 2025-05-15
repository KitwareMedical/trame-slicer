from __future__ import annotations

from slicer import vtkMRMLInteractionNode, vtkMRMLMarkupsFiducialNode


def test_can_load_scene_with_markups(
    a_slicer_app,
    a_threed_view,
    render_interactive,
    a_data_folder,
):
    assert a_slicer_app.io_manager.load_scene(a_data_folder.joinpath("markups_scene.mrb"))

    assert list(a_slicer_app.scene.GetNodesByClass("vtkMRMLMarkupsFiducialNode"))
    assert list(a_slicer_app.scene.GetNodesByClass("vtkMRMLMarkupsLineNode"))
    assert list(a_slicer_app.scene.GetNodesByClass("vtkMRMLMarkupsAngleNode"))
    assert list(a_slicer_app.scene.GetNodesByClass("vtkMRMLMarkupsCurveNode"))

    a_threed_view.reset_view()
    if render_interactive:
        a_threed_view.interactor().Start()


def test_markups_nodes_can_be_placed_interactively(
    a_slicer_app,
    a_threed_view,
    render_interactive,
):
    markups_node: vtkMRMLMarkupsFiducialNode = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
    markups_node.AddControlPointWorld([-60, -40, 44], "F")
    assert markups_node.GetDisplayNode() is not None
    markups_node.SetDisplayVisibility(True)

    a_slicer_app.markups_logic.SetActiveList(markups_node)
    a_slicer_app.markups_logic.StartPlaceMode(True)

    if render_interactive:
        a_threed_view.interactor().Start()


def test_markups_node_added_then_removed_from_scene_removes_displayable_node(
    a_slicer_app,
    a_threed_view,
    render_interactive,
):
    markups_node: vtkMRMLMarkupsFiducialNode = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
    markups_node.CreateDefaultDisplayNodes()
    markups_node.AddControlPointWorld([-60, -40, 44], "F")
    d_node = markups_node.GetDisplayNode()
    assert d_node is not None
    a_slicer_app.scene.RemoveNode(markups_node)
    assert a_slicer_app.scene.GetNodeByID(d_node.GetID()) is None
    if render_interactive:
        a_threed_view.interactor().Start()


def test_markups_logic_can_place_markups_lines(a_slicer_app, a_threed_view, render_interactive):
    assert a_threed_view
    markups_node = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLMarkupsLineNode")
    a_slicer_app.markups_logic.place_node(markups_node)

    assert a_slicer_app.markups_logic.interaction_node.GetCurrentInteractionMode() == vtkMRMLInteractionNode.Place

    if render_interactive:
        a_threed_view.interactor().Start()
