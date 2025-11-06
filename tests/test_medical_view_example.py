import pytest
from async_timeout import timeout
from playwright.async_api import async_playwright

from examples.medical_viewer_app import MedicalViewerApp


@pytest.mark.asyncio
async def test_medical_view_example_can_be_loaded(async_server, a_server_port):
    MedicalViewerApp(async_server)
    async_server.start(port=a_server_port, thread=True, exec_mode="task")

    async with timeout(30), async_playwright() as p:
        assert await async_server.ready
        assert async_server.port
        url = f"http://127.0.0.1:{async_server.port}/"
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await browser.close()
