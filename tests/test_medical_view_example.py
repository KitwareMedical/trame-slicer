from __future__ import annotations

import pytest
from playwright.async_api import async_playwright

from examples.medical_viewer_app import MyTrameSlicerApp


@pytest.mark.asyncio
async def test_medical_view_example_can_be_loaded(async_server, a_server_port):
    MyTrameSlicerApp(async_server)
    async_server.start(port=a_server_port, thread=True, exec_mode="task")
    assert await async_server.ready
    assert async_server.port

    async with async_playwright() as p:
        url = f"http://127.0.0.1:{async_server.port}/"
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await browser.close()
