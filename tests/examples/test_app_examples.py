import asyncio

import pytest
from async_timeout import timeout
from playwright.async_api import async_playwright

from examples.medical_viewer_app import MedicalViewerApp
from examples.segmentation_app import SegmentationApp


def min_example_apps() -> list[type]:
    import inspect

    import examples.minimal as min_examples

    return [obj for name, obj in inspect.getmembers(min_examples, inspect.isclass)]


@pytest.mark.parametrize("example_cls", [MedicalViewerApp, SegmentationApp, *min_example_apps()])
@pytest.mark.asyncio
async def test_example_app_can_be_loaded(async_server, a_server_port, example_cls):
    example_cls(async_server)
    async_server.start(port=a_server_port, thread=True, exec_mode="task")

    async with timeout(30), async_playwright() as p:
        assert await async_server.ready
        assert async_server.port
        url = f"http://127.0.0.1:{async_server.port}/"
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await asyncio.sleep(1.0)
        await browser.close()
