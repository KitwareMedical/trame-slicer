import pytest
from slicer import vtkMRMLAbstractViewNode, vtkMRMLNode, vtkMRMLScriptedModuleNode
from undo_stack import SignalContainerSpy, UndoStack

from trame_slicer.segmentation import (
    SegmentationEffect,
    SegmentationEffectNoTool,
    SegmentationEffectPaint,
    SegmentationEffectPipeline,
    SegmentationEffectScissors,
)
from trame_slicer.utils import vtk_image_to_np


@pytest.fixture
def editor(a_segmentation_editor):
    return a_segmentation_editor


@pytest.fixture
def undo_stack(editor):
    undo_stack = UndoStack()
    editor.set_undo_stack(undo_stack)
    return undo_stack


@pytest.fixture
def active_segmentation_node(editor, a_volume_node):
    segmentation_node = editor.create_empty_segmentation_node()
    editor.set_active_segmentation(segmentation_node, a_volume_node)
    return segmentation_node


@pytest.fixture
def editor_spy(editor):
    return SignalContainerSpy(editor)


def test_segmentation_editor_can_add_segments(editor, a_volume_node, active_segmentation_node):
    assert editor.get_segment_ids() == []

    editor.set_active_segmentation(active_segmentation_node, a_volume_node)
    editor.add_empty_segment(
        segment_id="segment_id_1",
        segment_name="SegmentName",
        segment_color=[1.0, 0.0, 0.0],
    )
    editor.add_empty_segment(
        segment_id="segment_id_2",
        segment_name="SegmentName2",
        segment_color=[0.0, 1.0, 0.0],
    )

    assert active_segmentation_node.GetSegmentation().GetNumberOfSegments() == 2
    assert editor.get_segment_ids() == ["segment_id_1", "segment_id_2"]
    assert editor.get_segment_names() == ["SegmentName", "SegmentName2"]


def test_segmentation_can_enable_3d_repr(editor, a_volume_node, a_segmentation_model):
    segmentation_node = editor.create_segmentation_node_from_model_node(a_segmentation_model)
    editor.set_surface_representation_enabled(True)
    editor.set_active_segmentation(segmentation_node, a_volume_node)
    assert segmentation_node.GetSegmentation().ContainsRepresentation(editor.active_segmentation._surface_repr_name)

    editor.set_surface_representation_enabled(False)
    assert not segmentation_node.GetSegmentation().ContainsRepresentation(editor.active_segmentation._surface_repr_name)


def test_segmentation_can_undo_modifications(
    editor,
    undo_stack,
    active_segmentation_node,
):
    assert active_segmentation_node
    for _ in range(5):
        editor.add_empty_segment()

    assert undo_stack.can_undo()
    undo_stack.undo()

    assert len(editor.get_segment_ids()) == 4
    assert undo_stack.can_redo()

    undo_stack.redo()
    assert len(editor.get_segment_ids()) == 5
    assert not undo_stack.can_redo()


@pytest.fixture
def segmentation_with_two_segments(editor, undo_stack, active_segmentation_node):
    assert undo_stack
    assert active_segmentation_node
    segment_id_1 = editor.add_empty_segment()

    vtk_modifier = editor.create_modifier_labelmap()
    modifier = vtk_image_to_np(vtk_modifier)
    modifier[0, 0, 0] = 1
    editor.active_segment_modifier.apply_labelmap(vtk_modifier)

    segment_id_2 = editor.add_empty_segment()
    modifier[0, 0, 0] = 0
    modifier[1, 0, 0] = 1
    editor.active_segment_modifier.apply_labelmap(vtk_modifier)
    return segment_id_1, segment_id_2


def test_modifying_segmentation_label_can_be_undo_redo(editor, undo_stack, segmentation_with_two_segments):
    segment_id_1, segment_id_2 = segmentation_with_two_segments
    assert editor.get_segment_labelmap(segment_id_1, as_numpy_array=True).sum() == 1
    assert editor.get_segment_labelmap(segment_id_2, as_numpy_array=True).sum() == 1

    assert undo_stack.can_undo()
    undo_stack.undo()

    assert editor.get_segment_labelmap(segment_id_1, as_numpy_array=True).sum() == 1
    assert editor.get_segment_labelmap(segment_id_2, as_numpy_array=True).sum() == 0

    while undo_stack.can_undo():
        undo_stack.undo()

    undo_stack.redo()
    assert editor.get_segment_labelmap(segment_id_1, as_numpy_array=True).sum() == 0

    assert undo_stack.can_redo()
    while undo_stack.can_redo():
        undo_stack.redo()

    assert editor.get_segment_labelmap(segment_id_1, as_numpy_array=True).sum() == 1
    assert editor.get_segment_labelmap(segment_id_2, as_numpy_array=True).sum() == 1


def test_undo_redo_keeps_labelmap_merged(editor, undo_stack, segmentation_with_two_segments):
    segment_id_1, segment_id_2 = segmentation_with_two_segments

    labelmap_1 = editor.get_segment_labelmap(segment_id_1)
    labelmap_2 = editor.get_segment_labelmap(segment_id_2)
    assert labelmap_1 == labelmap_2

    while undo_stack.can_undo():
        undo_stack.undo()

    while undo_stack.can_redo():
        undo_stack.redo()

    labelmap_1 = editor.get_segment_labelmap(segment_id_1)
    labelmap_2 = editor.get_segment_labelmap(segment_id_2)
    assert labelmap_1 == labelmap_2


def test_undo_redo_keeps_labelmap_merged_after_remove(editor, undo_stack, segmentation_with_two_segments, editor_spy):
    segment_id_1, segment_id_2 = segmentation_with_two_segments
    editor_spy.reset()

    editor.remove_segment(segment_id_2)
    undo_stack.undo()

    labelmap_1 = editor.get_segment_labelmap(segment_id_1)
    labelmap_2 = editor.get_segment_labelmap(segment_id_2)
    assert labelmap_1 == labelmap_2

    assert editor.get_segment_labelmap(segment_id_1, as_numpy_array=True).sum() > 0
    assert editor.get_segment_labelmap(segment_id_2, as_numpy_array=True).sum() > 0
    editor_spy[editor.segmentation_modified].assert_called()


def test_notifies_changes_on_new_segmentation(editor, a_volume_node, editor_spy):
    n1 = editor.create_empty_segmentation_node()

    editor.set_active_segmentation(n1, a_volume_node)
    editor_spy[editor.active_segment_id_changed].assert_called_with("")
    editor_spy[editor.show_3d_changed].assert_called_with(False)
    editor_spy[editor.active_effect_name_changed].assert_called_with(SegmentationEffectNoTool.get_effect_name())
    editor_spy.reset()

    editor.show_3d(True)
    editor_spy[editor.show_3d_changed].assert_called_with(True)

    segment_id = editor.add_empty_segment()
    editor_spy[editor.active_segment_id_changed].assert_called_with(segment_id)

    effect = editor.set_active_effect_type(SegmentationEffectScissors)
    editor_spy[editor.active_effect_name_changed].assert_called_with(effect.get_effect_name())

    editor_spy.reset()
    editor.remove_segment(segment_id)

    editor_spy[editor.active_segment_id_changed].assert_called_with("")
    editor_spy[editor.active_effect_name_changed].assert_called_with(SegmentationEffectNoTool.get_effect_name())


def test_can_add_new_effects_to_segmentation_editor_by_type(editor, a_threed_view):
    class MyEffectPipeline(SegmentationEffectPipeline):
        pass

    class MyNewEffect(SegmentationEffect):
        def _create_pipeline(
            self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
        ) -> SegmentationEffectPipeline | None:
            return MyEffectPipeline()

    editor.register_effect_type(MyNewEffect)
    effect = editor.set_active_effect_type(MyNewEffect)

    assert effect.pipelines
    assert isinstance(effect.pipelines[0](), MyEffectPipeline)
    assert effect.pipelines[0]().GetViewNode() == a_threed_view.get_view_node()
    assert effect.is_active


def test_can_return_segmentation_effect_type_parameter_node(editor):
    param = editor.get_effect_parameter_node(SegmentationEffectPaint)
    assert isinstance(param, vtkMRMLScriptedModuleNode)


def test_can_return_segmentation_effect_parameter_node(editor):
    class MyEffectPipeline(SegmentationEffectPipeline):
        pass

    p = vtkMRMLScriptedModuleNode()

    class MyNewEffect(SegmentationEffect):
        def _create_pipeline(
            self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
        ) -> SegmentationEffectPipeline | None:
            return MyEffectPipeline()

        def get_parameter_node(self):
            return p

    editor.register_effect_type(MyNewEffect)
    editor.set_active_effect_type(MyNewEffect)
    assert editor.get_effect_parameter_node(editor.active_effect) == p


def test_registers_effect_when_accessing_effect_parameter_node_if_needed(editor):
    class MyEffectPipeline(SegmentationEffectPipeline):
        pass

    class MyNewEffect(SegmentationEffect):
        def _create_pipeline(
            self, _view_node: vtkMRMLAbstractViewNode, _parameter: vtkMRMLNode
        ) -> SegmentationEffectPipeline | None:
            return MyEffectPipeline()

    assert not editor.is_effect_type_registered(MyNewEffect)
    assert editor.get_effect_parameter_node(MyNewEffect)
    assert editor.is_effect_type_registered(MyNewEffect)


def test_scene_clear_clears_segmentation_stack(editor, a_slicer_app, undo_stack, active_segmentation_node):
    assert active_segmentation_node
    editor.add_empty_segment()
    assert undo_stack.can_undo()
    a_slicer_app.scene.Clear()
    assert not undo_stack.can_undo()


def test_scene_clear_without_undo_stack_does_nothing(editor, a_slicer_app):
    assert editor.undo_stack is None
    a_slicer_app.scene.Clear()
