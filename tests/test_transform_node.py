import pytest

from tests.conftest import a_slice_view, a_threed_view


@pytest.mark.parametrize("view", [a_threed_view, a_slice_view])
def test_linear_transform_widget_can_be_displayed_in_views(view, request, a_slicer_app, render_interactive):
    view = request.getfixturevalue(view.__name__)

    transform_node = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLLinearTransformNode")
    assert transform_node

    transform_node.CreateDefaultDisplayNodes()
    display_node = transform_node.GetDisplayNode()
    assert display_node

    display_node.SetEditorVisibility(True)

    if render_interactive:
        view.start_interactor()
