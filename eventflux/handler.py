import abc
import functools
import typing
import inspect

import eventflux.event


class HandlerAbstractClass(abc.ABC):
    @abc.abstractmethod
    async def handle_if_match(self, event: eventflux.event.CloudEvent):
        raise NotImplementedError


class Handler:
    def __init__(self, type: str, func: typing.Callable):
        self.type = type
        self.func = func
        self._awaitable = False
        self._analyze_handler_func()

    def _analyze_handler_func(self):
        signature = inspect.signature(self.func)

        if "event" not in signature.parameters:
            raise ValueError(f"missing event on handler {self.func.__name__}")

        self._awaitable = inspect.iscoroutinefunction(self.func)

    @functools.lru_cache
    def _can_handle(self, type: str) -> bool:
        return type == self.type

    async def _handle(self, event: eventflux.event.CloudEvent):
        if self._awaitable:
            return await self.func(event=event)
        return self.func(event=event)

    async def handle_if_match(self, event: eventflux.event.CloudEvent):
        if self._can_handle(type=event.type):
            await self._handle(event=event)
