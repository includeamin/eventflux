import asyncio
import typing
from collections.abc import Callable
from typing import Any

import eventflux.event
import eventflux.handler

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])


class CloudEventRouter:
    def __init__(self) -> None:
        self.handlers: dict[str, eventflux.handler.CloudEventHandler] = {}

    def on_event(self, type: str) -> Callable[[Callable[..., Any]], Any]:
        def wrapper(func: typing.Callable[..., typing.Any]) -> typing.Any:
            _handler = eventflux.handler.CloudEventHandler(type=type, func=func)
            self.handlers.update({type: _handler})

        return wrapper

    def _can_route(self, type: str) -> bool:
        return type in self.handlers

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
