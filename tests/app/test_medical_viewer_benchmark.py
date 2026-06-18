import asyncio
import os
from pathlib import Path

import pytest
import yappi
from playwright.sync_api import sync_playwright

from trame_slicer.app.medical_viewer_app import MedicalViewerApp


def run_slice_slider_benchmark(benchmark, port, benchmark_path):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(f"http://127.0.0.1:{port}/")
        sliders = page.locator(".slice-slider .v-slider-thumb")
        sliders.first.wait_for()
        assert sliders.count() == 3
        page.wait_for_timeout(1000)
        direction = 1
        drag_cycles = int(os.environ.get("TRAME_SLICER_BENCHMARK_DRAG_CYCLES", "3"))

        def move_slice_sliders():
            nonlocal direction

            for _ in range(drag_cycles):
                direction *= -1

                for index in range(sliders.count()):
                    slider = sliders.nth(index)
                    thumb_box = slider.bounding_box()
                    track_box = page.locator(".slice-slider").nth(index).bounding_box()
                    assert thumb_box is not None
                    assert track_box is not None

                    start_x = thumb_box["x"] + thumb_box["width"] / 2
                    start_y = thumb_box["y"] + thumb_box["height"] / 2
                    end_x = track_box["x"] + track_box["width"] * (0.75 if direction == 1 else 0.25)

                    page.mouse.move(start_x, start_y)
                    page.mouse.down()
                    page.mouse.move(end_x, start_y, steps=20)
                    page.mouse.up()

        with yappi.run():
            benchmark.pedantic(
                move_slice_sliders,
                rounds=5,
                iterations=1,
            )
        info = yappi.get_func_stats()
        info.save(benchmark_path, type="ystat")
        browser.close()


@pytest.mark.asyncio
async def test_medical_viewer_slice_slider_benchmark(
    benchmark,
    async_server,
    a_server_port,
    a_nrrd_volume_file_path,
    tmpdir,
    capsys,
):
    app = MedicalViewerApp(async_server)
    app._logic._load_files_logic._on_load_volume_files([a_nrrd_volume_file_path.as_posix()])
    app._logic.layout_manager.set_layout("Quad View")
    async_server.start(port=a_server_port, thread=True, exec_mode="task")
    await async_server.ready

    yappi_path = Path(tmpdir) / "slider_benchmark.ystat"
    await asyncio.to_thread(run_slice_slider_benchmark, benchmark, async_server.port, yappi_path.as_posix())

    with capsys.disabled():
        print(f"Yappi profile written to: {yappi_path.resolve()}")
