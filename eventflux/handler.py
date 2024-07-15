import inspect
import typing

import eventflux.event


class CloudEventHandler:
    def __init__(
        self,
        func: typing.Callable,
    ):
        self.func = func
        self._awaitable = False
        self._analyze_handler_func()

    def _analyze_handler_func(self) -> None:
        signature = inspect.signature(self.func)

        if "event" not in signature.parameters:
            raise ValueError(f"missing event on handler {self.func.__name__}")

        self._awaitable = inspect.iscoroutinefunction(self.func)

    async def handle(self, event: eventflux.event.CloudEvent):
        if self._awaitable:
            return await self.func(event=event)
        return self.func(event=event)
