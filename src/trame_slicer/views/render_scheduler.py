from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from trame_server.utils import asynchronous

if TYPE_CHECKING:
    from .abstract_view import AbstractView


class ScheduledRenderStrategy:
    """
    Abstract class for handling scheduled rendering.
    Rendering update is triggered by Slicer's display managers.
    In asyncio context, the update can be managed using asyncio Tasks.
    In specific event loops, such as Qt, the rendering can be done using QTimer.
    """

    def __init__(self):
        self.abstract_view: AbstractView | None = None

    def schedule_render(self):
        pass

    def did_render(self):
        pass

    def set_abstract_view(self, abstract_view: AbstractView):
        self.abstract_view = abstract_view


class NoScheduleRendering(ScheduledRenderStrategy):
    pass


class DirectRendering(ScheduledRenderStrategy):
    def schedule_render(self):
        if self.abstract_view:
            self.abstract_view.render()


class AsyncIORendering(ScheduledRenderStrategy):
    def __init__(self, schedule_render_fps: float = 30.0):
        super().__init__()
        self.request_render_task: asyncio.Task | None = None
        self.schedule_render_fps = schedule_render_fps

    def schedule_render(self):
        if self.request_render_task is None:
            self.request_render_task = asynchronous.create_task(self._async_render())
            self.request_render_task.add_done_callback(self.cleanup_render_task)

    async def _async_render(self):
        await asyncio.sleep(1.0 / self.schedule_render_fps)
        if self.abstract_view:
            self.abstract_view.render()

    def did_render(self):
        if self.request_render_task is not None:
            self.request_render_task.cancel()
            self.request_render_task = None

    def cleanup_render_task(self, *_):
        self.request_render_task = None
