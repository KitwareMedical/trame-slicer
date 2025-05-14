from __future__ import annotations

import pytest

from trame_slicer.utils import SlicerWrapper, wrap


def test_wraps_slicer_obj_function_calls(a_slicer_app):
    model_node = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode")
    model_node.SetName("New Name")
    wrapped_model = wrap(model_node)

    assert model_node.GetID() == wrapped_model.GetID()
    assert model_node.GetScene() == wrapped_model.GetScene()
    assert wrapped_model.GetName() == "New Name"


def test_modifying_through_wrapper_changes_mrml_values(a_slicer_app):
    model = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode")
    model.SetName("PLOP")
    model_node = wrap(model)
    model_node.SetName("New Name")
    model_node = a_slicer_app.scene.GetNodeByID(model_node.GetID())
    assert model_node.GetName() == "New Name"


def test_auto_converts_from_snake_case_to_pascal(a_slicer_app):
    wrapped_model = wrap(a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode"))
    wrapped_model.set_name("New Name")
    assert wrapped_model.get_name() == "New Name"


def test_raises_attribute_error_for_invalid_snake_case_attribute(a_slicer_app):
    wrapped_model = wrap(a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode"))
    with pytest.raises(AttributeError):
        wrapped_model.not_a_method_in_class()


def test_raises_attribute_error_for_invalid_pascal_case_attribute(a_slicer_app):
    wrapped_model = wrap(a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode"))
    with pytest.raises(AttributeError):
        wrapped_model.NotAMethodInClass()


def test_can_be_used_in_inheritance(a_slicer_app):
    class MyModelNode(SlicerWrapper):
        def my_name(self):
            return "MyPrefix " + self.get_name()

    model_node = a_slicer_app.scene.AddNewNodeByClass("vtkMRMLModelNode")
    model_node.SetName("New Name")

    wrapped_model = MyModelNode(model_node)

    assert model_node.GetID() == wrapped_model.GetID()
    assert model_node.GetScene() == wrapped_model.GetScene()
    assert wrapped_model.my_name() == "MyPrefix New Name"


def test_errors_when_fetching_information_are_informative():
    class MyModelNode(SlicerWrapper):
        @property
        def my_name_property(self):
            return "MyPrefix " + self.get_name()

    wrapped_model = MyModelNode(None)
    with pytest.raises(AttributeError) as exc_info:
        print(wrapped_model.my_name_property)

    assert "None" in str(exc_info.value)
    assert "my_name_property" in str(exc_info.value)
