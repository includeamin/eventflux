import asyncio
import signal

import time
import uuid

import eventflux.subscribers.base
import eventflux.router
import structlog

log = structlog.get_logger()


class App:
    def __init__(self, identifier: str = None):
        self.identifier = str(uuid.uuid4()) if not identifier else identifier
        self.routers: list[type[eventflux.router.RouterAbstractClass]] = []
        self.subscribers: list[
            type[eventflux.subscribers.base.SubscriberAbstractClass]
        ] = []
        self._in_progress_events = {}
        self._must_exit = False

    def mount_router(self, router: type[eventflux.router.RouterAbstractClass]):
        self.routers.append(router)

    def mount_subscriber(
        self, subscriber: type[eventflux.subscribers.base.SubscriberAbstractClass]
    ):
        self.subscribers.append(subscriber)

    async def _process_events(self, queue: asyncio.Queue):
        log.info("start processing events")
        while True:
            if self._must_exit:
                log.info(
                    "worker has been stopped",
                    in_progress_events_count=len(self._in_progress_events),
                )
                break
            if queue.empty():
                log.debug("empty queue is detected, waiting for input")
                await asyncio.sleep(0.01)
                continue
            event = await queue.get()
            task = asyncio.create_task(self.handle(event=event))
            self._in_progress_events[id(event)] = task
            await asyncio.sleep(0.01)

    async def _start_listening(
        self, queue: asyncio.Queue, subscriber: type[eventflux.subscribers.base]
    ):
        log.info("fir up all listeners", lesteners_count=len(self.subscribers))
        async for event in subscriber.listening():
            if self._must_exit:
                log.info("stop listening")
                break
            await queue.put(event)
            log.debug(
                "task has been added to the queue",
                event_id=event.id,
                total_in_progress_task=len(self._in_progress_events),
            )
            await asyncio.sleep(0.01)

    async def handle(self, event):
        start_time = time.time()
        tasks = [router.route_if_match(event=event) for router in self.routers]
        await asyncio.gather(*tasks)
        end_time = time.time()
        log.info(
            "event has been processed",
            type=event.type,
            duration=(end_time - start_time) * 1000,
        )
        self._in_progress_events.pop(id(event))

    def run(self):
        asyncio.run(self.async_app())

    def finish(self):
        self._must_exit = True

    async def _monitor_in_progress_tasks(self):
        while True:
            if self._must_exit:
                log.info(
                    "waiting for all tasks to be finished",
                    total_in_progress_tasks=len(self._in_progress_events),
                )
                await asyncio.gather(
                    *[task for task in self._in_progress_events.values()]
                )
                log.info("Bye!")
                break
            await asyncio.sleep(0.1)

    async def async_app(self):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, self.finish)
        queue = asyncio.Queue()
        await asyncio.gather(
            self._process_events(queue=queue),
            self._start_listening(subscriber=self.subscribers[0], queue=queue),
            self._monitor_in_progress_tasks(),
        )
