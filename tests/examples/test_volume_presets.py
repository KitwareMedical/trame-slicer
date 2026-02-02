from trame_server.utils.typed_state import TypedState

from examples.medical_viewer_app import MedicalViewerApp
from examples.viewer_lib.ui import VolumePropertyState
from trame_slicer.core.volume_window_level import VolumeWindowLevel


def test_presets_2d_populated(a_server):
    MedicalViewerApp(a_server)
    typed_state = TypedState(a_server.state, VolumePropertyState)
    assert len(typed_state.data.presets_2d) > 0


def test_presets_3d_populated(a_server):
    MedicalViewerApp(a_server)
    typed_state = TypedState(a_server.state, VolumePropertyState)
    assert len(typed_state.data.presets_3d) > 0


def test_setting_2d_preset_changes_window_level(a_server, a_volume_node):
    app = MedicalViewerApp(a_server)
    typed_state = TypedState(a_server.state, VolumePropertyState)
    assert typed_state.data.preset_2d_name is None

    app._logic._volume_properties_logic.on_volume_changed(a_volume_node)  # Manually load node
    window_level = typed_state.data.window_level_slider.value

    preset_name = "CT_AIR"
    assert preset_name in [preset.title for preset in typed_state.data.presets_2d]
    volume_display_node = VolumeWindowLevel.get_volume_display_node(a_volume_node)
    app._slicer_app.volumes_logic.ApplyVolumeDisplayPreset(volume_display_node, preset_name)

    assert typed_state.data.window_level_slider.value != window_level
