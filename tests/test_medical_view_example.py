from __future__ import annotations

import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.parametrize("server_path", ["examples/medical_viewer_app.py"])
def test_medical_view_example_can_be_loaded(a_subprocess_server):
    assert a_subprocess_server.port

    with sync_playwright() as p:
        url = f"http://127.0.0.1:{a_subprocess_server.port}/"
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
