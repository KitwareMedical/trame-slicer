from __future__ import annotations

from trame_slicer.core import VolumeWindowLevel


def test_returns_scalar_range_of_volume(a_volume_node):
    assert VolumeWindowLevel.get_volume_scalar_range(a_volume_node) == (0, 279)


def test_returns_auto_range_of_volume(a_volume_node):
    assert VolumeWindowLevel.get_volume_auto_min_max_range(a_volume_node) == (0, 151)


def test_can_set_volume_display_range(a_volume_node):
    VolumeWindowLevel.set_volume_node_display_min_max_range(a_volume_node, 1, 15)
    assert VolumeWindowLevel.get_volume_display_range(a_volume_node) == (1, 15)


def test_can_convert_min_max_to_window_level():
    assert VolumeWindowLevel.min_max_to_window_level(150, 0) == (150, 75)
