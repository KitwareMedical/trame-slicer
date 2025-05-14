from __future__ import annotations

import pytest
from seleniumbase import SB


@pytest.mark.parametrize("server_path", ["examples/medical_viewer_app.py"])
def test_medical_view_example_can_be_loaded(a_subprocess_server):
    with SB() as sb:
        assert a_subprocess_server.port

        url = f"http://127.0.0.1:{a_subprocess_server.port}/"
        sb.open(url)
