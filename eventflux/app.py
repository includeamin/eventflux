import asyncio

import time
import uuid

import eventflux.subscribers.base
import eventflux.router
import structlog

log = structlog.get_logger()


class App:
    routers: list[eventflux.router.Router]
    subscribers: list[type[eventflux.subscribers.base.SubscriberAbstractClass]]

    def __init__(self, identifier: str = None):
        self.identifier = str(uuid.uuid4()) if not identifier else identifier
        self.routers = []
        self.subscribers = []

    def mount_router(self, router: eventflux.router.Router):
        self.routers.append(router)

    def mount_subscriber(
        self, subscriber: type[eventflux.subscribers.base.SubscriberAbstractClass]
    ):
        self.subscribers.append(subscriber)

    async def _execute(self, subscriber: type[eventflux.subscribers.base]):
        async for event in subscriber.listening():
            start_time = time.time()

            tasks = [
                asyncio.create_task(router.route_if_match(event=event))
                for router in self.routers
            ]
            await asyncio.gather(*tasks)
            end_time = time.time()

            log.info(
                "event has been processed",
                type=event.type,
                duration=(end_time - start_time) * 1000,
            )

    def run(self):
        asyncio.run(self.async_app())

    async def async_app(self):
        tasks = [
            self._execute(subscriber=subscriber) for subscriber in self.subscribers
        ]
        await asyncio.gather(*tasks)
