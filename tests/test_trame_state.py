from __future__ import annotations

from unittest.mock import MagicMock


def test_trame_state_change_can_be_hooked_to_string_callback(a_server):
    custom_string = "my_custom_string"
    mock = MagicMock()

    @a_server.state.change(custom_string)
    def decorated(*_, **kwargs):
        mock(kwargs[custom_string])

    a_server.state.ready()
    a_server.state[custom_string] = 42
    a_server.state.flush()
    mock.assert_called_with(42)
