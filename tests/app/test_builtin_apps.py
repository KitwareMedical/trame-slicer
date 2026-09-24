import asyncio

import pytest
from async_timeout import timeout
from playwright.async_api import async_playwright

from tests import smoke_test_trame_app
from trame_slicer.app import MedicalViewerApp, SegmentationApp


def builtin_apps():
    return [MedicalViewerApp, SegmentationApp]


@pytest.mark.parametrize("builtin_app", builtin_apps())
@pytest.mark.asyncio
async def test_builtin_app_can_be_loaded(async_server, unused_tcp_port, builtin_app):
    await smoke_test_trame_app(async_server, unused_tcp_port, builtin_app)


@pytest.mark.parametrize("builtin_app", builtin_apps())
@pytest.mark.asyncio
async def test_builtin_apps_can_load_volume_files(
    builtin_app,
    async_server,
    unused_tcp_port,
    a_background_volume_file_path,
    a_foreground_volume_file_path,
    a_nrrd_volume_file_path,
):
    app = builtin_app(async_server)
    async_server.start(port=unused_tcp_port, exec_mode="task")

    async with timeout(30), async_playwright() as playwright:
        assert await async_server.ready
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"http://127.0.0.1:{async_server.port}/")
        await page.wait_for_function("typeof window.load_files_by_chunks === 'function'")
        await page.locator('input[type="file"]').first.set_input_files(
            [
                a_background_volume_file_path,
                a_foreground_volume_file_path,
                a_nrrd_volume_file_path,
            ]
        )

        while app._slicer_app.scene.GetNumberOfNodesByClass("vtkMRMLVolumeNode") != 3:
            await asyncio.sleep(0.1)

        await browser.close()
