"""
Simple asyncio-based reminder scheduler stub.

Replace with Celery/RQ/Cloud Tasks in production. No external API calls here.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Awaitable, Dict


class Scheduler:
    def __init__(self) -> None:
        self._queue: "asyncio.PriorityQueue[tuple[float, Callable[[], Awaitable[None]]]]" = asyncio.PriorityQueue()
        self._task: asyncio.Task | None = None
        self._running = False

    async def _runner(self) -> None:
        self._running = True
        while self._running:
            when, coro_factory = await self._queue.get()
            delay = max(0.0, when - asyncio.get_event_loop().time())
            await asyncio.sleep(delay)
            try:
                await coro_factory()
            except Exception:  # pragma: no cover – log in real service
                pass

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._runner())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    def schedule(self, delay: timedelta, coro_factory: Callable[[], Awaitable[None]]) -> None:
        when = asyncio.get_event_loop().time() + delay.total_seconds()
        self._queue.put_nowait((when, coro_factory))


SCHEDULER = Scheduler()


async def remind_job_upcoming(job_id: int) -> None:
    # TODO: integrate email/SMS/Push provider here.
    # For MVP, we no-op or log.
    _ = job_id
    return None

