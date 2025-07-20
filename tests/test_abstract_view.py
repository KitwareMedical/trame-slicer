from __future__ import annotations

from unittest import mock

import pytest
import vtk
from slicer import (
    vtkMRMLCameraDisplayableManager,
    vtkMRMLDisplayableManagerGroup,
    vtkMRMLThreeDViewDisplayableManagerFactory,
    vtkMRMLVolumeRenderingDisplayableManager,
)

from trame_slicer.views import AbstractView, ScheduledRenderStrategy


@pytest.fixture
def mocked_schedule_render() -> ScheduledRenderStrategy:
    return mock.create_autospec(ScheduledRenderStrategy)


def test_abstract_view_can_render_a_simple_cone():
    view = AbstractView()
    cone, mapper, actor = vtk.vtkConeSource(), vtk.vtkPolyDataMapper(), vtk.vtkActor()

    cone.Update()
    mapper.SetInputConnection(cone.GetOutputPort())
    actor.SetMapper(mapper)

    view.render_window()
    view.first_renderer().AddActor(actor)
    view.first_renderer().ResetCamera()
    view.render()


def test_abstract_view_can_block_render(mocked_schedule_render):
    view = AbstractView()
    view.set_scheduled_render(mocked_schedule_render)
    was_blocked = view.set_render_blocked(True)
    assert not was_blocked
    view.schedule_render()
    mocked_schedule_render.schedule_render.assert_not_called()

    view.set_render_blocked(was_blocked)
    mocked_schedule_render.schedule_render.assert_called()


def test_abstract_view_render_block_can_be_done_usign_context_manager(mocked_schedule_render):
    view = AbstractView()
    view.set_scheduled_render(mocked_schedule_render)

    with view.render_blocked():
        view.schedule_render()
        mocked_schedule_render.schedule_render.assert_not_called()

    mocked_schedule_render.schedule_render.assert_called()


def test_displayable_manager_group_can_use_displayable_string_instantiation():
    ruler_displayable_manager = vtkMRMLDisplayableManagerGroup.InstantiateDisplayableManager(
        "vtkMRMLRulerDisplayableManager"
    )
    assert ruler_displayable_manager is not None


def test_displayable_group_can_be_initialized_by_factories(a_slicer_app):
    managers = [
        vtkMRMLVolumeRenderingDisplayableManager,
        vtkMRMLCameraDisplayableManager,
    ]

    # Don't use singleton for test
    factory = vtkMRMLThreeDViewDisplayableManagerFactory()
    factory.SetMRMLApplicationLogic(a_slicer_app.app_logic)
    for manager in managers:
        if not factory.IsDisplayableManagerRegistered(manager.__name__):
            assert factory.RegisterDisplayableManager(manager.__name__)

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    displayable_manager_group = vtkMRMLDisplayableManagerGroup()
    displayable_manager_group.Initialize(factory, renderer)
    assert displayable_manager_group.GetDisplayableManagerCount() == 2
