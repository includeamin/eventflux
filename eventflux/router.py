import abc
import asyncio
import functools

import eventflux.handler
import eventflux.event


class RouterAbstractClass(abc.ABC):
    @abc.abstractmethod
    def on_event(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    async def route_if_match(self, event: eventflux.event.BaseEvent):
        raise NotImplementedError


class CloudEventRouter(RouterAbstractClass):
    def __init__(self):
        self.handlers: dict[str, eventflux.handler.HandlerAbstractClass] = {}

    def on_event(self, type: str):
        def wrapper(func):
            _handler = eventflux.CloudEventHandler(type=type, func=func)
            self.handlers.update({type: _handler})

        return wrapper

    @functools.lru_cache
    def _can_route(self, type: str) -> bool:
        return type in self.handlers.keys()

    async def _route(self, event: eventflux.event.CloudEvent):
        await asyncio.gather(
            *[
                handler.handle_if_match(event=event)
                for handler in self.handlers.values()
            ]
        )

    async def route_if_match(self, event: eventflux.event.CloudEvent):
        if self._can_route(type=event.type):
            await self._route(event=event)
