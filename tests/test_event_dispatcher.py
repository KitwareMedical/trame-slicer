from __future__ import annotations

import gc
from unittest.mock import MagicMock
from weakref import ref

from vtkmodules.vtkFiltersSources import vtkSphereSource

from trame_slicer.utils.vtk_event_dispatcher import VtkEventDispatcher


class AClass:
    """
    Test class to mimic bound / unbound methods when dispatching.
    """

    def __init__(self):
        self.mock = MagicMock()

    def method(self, *args, **kwargs):
        self.mock(*args, **kwargs)


def test_dispatcher_is_compatible_with_bound_observers():
    inst = AClass()

    sphere = vtkSphereSource()
    dispatcher = VtkEventDispatcher()
    dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")
    dispatcher.add_dispatch_observer(inst.method)

    sphere.SetRadius(42.0)
    inst.mock.assert_called()


def test_dispatcher_is_compatible_with_lambda_observers():
    inst = AClass()

    sphere = vtkSphereSource()
    dispatcher = VtkEventDispatcher()
    dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")
    dispatcher.add_dispatch_observer(lambda: inst.method())

    sphere.SetRadius(42.0)
    inst.mock.assert_called()


def test_dispatcher_can_attach_to_multiple_vtk_objects():
    spheres = [vtkSphereSource() for _ in range(4)]
    dispatcher = VtkEventDispatcher()
    for s in spheres:
        dispatcher.attach_vtk_observer(s, "ModifiedEvent")

    inst = AClass()
    dispatcher.add_dispatch_observer(inst.method)

    for s in spheres:
        s.SetRadius(2.0)

    assert inst.mock.call_count == len(spheres)


def test_dispatcher_dispatches_to_multiple_observers():
    sphere = vtkSphereSource()
    dispatcher = VtkEventDispatcher()
    dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")

    instances = [AClass() for _ in range(4)]
    for inst in instances:
        dispatcher.add_dispatch_observer(inst.method)

    sphere.SetRadius(2.0)
    assert all(inst.mock.called for inst in instances)


def test_dispatcher_does_nothing_if_bound_observers_deleted():
    inst = AClass()
    weak_mock = ref(inst)

    sphere = vtkSphereSource()
    dispatcher = VtkEventDispatcher()
    dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")
    dispatcher.add_dispatch_observer(inst.method)

    # Remove mock and make sure it was correctly removed
    del inst
    gc.collect()
    assert weak_mock() is None

    # Make sure calling update doesn't cause problems
    sphere.SetRadius(42.0)


def test_dispatcher_can_detach_from_vtk_object():
    inst = AClass()

    s1 = vtkSphereSource()
    s2 = vtkSphereSource()
    dispatcher = VtkEventDispatcher()

    obs_id = dispatcher.attach_vtk_observer(s1, "ModifiedEvent")
    dispatcher.attach_vtk_observer(s2, "ModifiedEvent")

    dispatcher.add_dispatch_observer(inst.method)
    dispatcher.detach_vtk_observer(obs_id)

    s1.SetRadius(42.0)
    inst.mock.assert_not_called()
    s2.SetRadius(42.0)
    inst.mock.assert_called()


def test_dispatcher_does_nothing_if_detaching_from_deleted_vtk_objects():
    sphere = vtkSphereSource()
    weak_sphere = ref(sphere)
    dispatcher = VtkEventDispatcher()

    obs_id = dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")

    # Delete sphere and make sure object has been correctly garbage collected
    del sphere
    gc.collect()
    assert weak_sphere() is None

    # Make sure nothing happens when removing obs id
    dispatcher.detach_vtk_observer(obs_id)


def test_dispatcher_sends_defined_dispatch_info_to_observers_on_observed_vtk_events():
    inst = AClass()

    sphere = vtkSphereSource()
    dispatcher = VtkEventDispatcher()
    dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")
    dispatcher.add_dispatch_observer(inst.method)
    dispatcher.set_dispatch_information(4, value=5)

    sphere.SetRadius(42.0)
    inst.mock.assert_called_with(4, value=5)


def test_dispatcher_can_unobserve_bound_observers():
    inst = AClass()

    sphere = vtkSphereSource()
    dispatcher = VtkEventDispatcher()
    dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")
    dispatcher.add_dispatch_observer(inst.method)
    dispatcher.remove_dispatch_observer(inst.method)

    sphere.SetRadius(42.0)
    inst.mock.assert_not_called()


def test_dispatcher_can_unobserve_unbound_observers():
    mock = MagicMock()

    sphere = vtkSphereSource()
    dispatcher = VtkEventDispatcher()
    dispatcher.attach_vtk_observer(sphere, "ModifiedEvent")
    dispatcher.add_dispatch_observer(mock)
    dispatcher.remove_dispatch_observer(mock)

    sphere.SetRadius(42.0)
    mock.assert_not_called()
