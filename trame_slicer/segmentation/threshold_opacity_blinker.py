from __future__ import annotations

import asyncio

from undo_stack import Signal


class ThresholdOpacityBlinker:
    opacity_changed = Signal(float)

    def __init__(self):
        self._blink_opacity_min = 0.5
        self._blink_opacity_max = 1.0
        self._preview_update_period_s = 0.2
        self._preview_steps = 6
        self._preview_state = 0
        self._preview_direction = 1
        self._preview_task: asyncio.Task | None = None

    def set_active(self, is_active: bool) -> None:
        if not is_active:
            self.stop()
        else:
            self.start()

    def set_opacity_range(self, low: float, high: float):
        self._blink_opacity_min = low
        self._blink_opacity_max = high

    def start(self):
        if self._preview_task is None:
            loop = asyncio.get_event_loop()
            self._preview_task = loop.create_task(self._update_preview_state())

    def stop(self):
        if self._preview_task is not None:
            self._preview_task.cancel()
            self._preview_task = None
            self._preview_state = 0

    async def _update_preview_state(self):
        while True:
            await asyncio.sleep(self._preview_update_period_s)
            self._preview_state += self._preview_direction
            if self._preview_state >= self._preview_steps or self._preview_state < 0:
                self._preview_direction *= -1
                self._preview_state += 2 * self._preview_direction
            self._preview_state = max(0, min(self._preview_steps - 1, self._preview_state))
            opacity_range = self._blink_opacity_max - self._blink_opacity_min
            opacity = self._blink_opacity_min + opacity_range * self._preview_state / (self._preview_steps - 1)
            self.opacity_changed(opacity)
