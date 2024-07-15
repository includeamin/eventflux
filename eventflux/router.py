import asyncio
import typing
from collections.abc import Callable
from typing import Any

import eventflux.event
import eventflux.handler


def _validate_filters(type: str | None = None, types: list[str] | None = None) -> None:
    if not types and not type:
        raise ValueError("at least one of the filters mut be set")
    if types and type:
        raise ValueError("only one of the filters must be set")


class CloudEventRouter:
    def __init__(self) -> None:
        self.handlers: dict[str, list[eventflux.handler.CloudEventHandler]] = {}

    def on_event(
        self, type: str | None = None, types: list[str] | None = None
    ) -> Callable[[Callable[..., Any]], Any]:
        _validate_filters(type, types)

        def wrapper(func: typing.Callable[..., typing.Any]) -> typing.Any:
            _handler = eventflux.handler.CloudEventHandler(func=func)

            if type:
                self._register_handler(type=type, handler=_handler)
            if types:
                for _type in types:
                    self._register_handler(type=_type, handler=_handler)

        return wrapper

    def _register_handler(
        self, type: str, handler: eventflux.handler.CloudEventHandler
    ) -> None:
        _registered_handlers = self.handlers.get(type, [])
        if _registered_handlers:
            _registered_handlers.append(handler)
        else:
            self.handlers.update({type: [handler]})

    def _can_route(self, event: eventflux.event.CloudEvent) -> bool:
        return self.handlers.get(event.type) is not None

    def _handlers_for_event(
        self, event: eventflux.event.CloudEvent
    ) -> list[eventflux.handler.CloudEventHandler]:
        return self.handlers.get(event.type, [])

    async def _route(self, event: eventflux.event.CloudEvent):
        await asyncio.gather(
            *[
                handler.handle(event=event)
                for handler in self._handlers_for_event(event=event)
            ]
        )

    async def route_if_match(self, event: eventflux.event.CloudEvent):
        if self._can_route(event=event):
            await self._route(event=event)
