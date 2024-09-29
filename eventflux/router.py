import asyncio
import typing
from collections.abc import Callable
from typing import Any

import jsonata

import eventflux.event
import eventflux.handler


class GenericEventRouter:
    def __init__(self) -> None:
        self.handlers: dict[str, list[dict[str, Any]]] = {}

    def on_event(
        self,
        content_type: typing.Literal["application/json"] = "application/json",
        jsonata_expr: str | None = None,
    ) -> Callable[[Callable[..., Any]], Any]:
        """
        Registers event handlers, allowing filters to be defined either via kwargs or direct JSONPath.
        """

        if not jsonata_expr:
            raise ValueError("jsonata expression is required")

        compiled_jsonata_expr = jsonata.Jsonata(jsonata_expr)

        def decorator(func: Callable[..., Any]) -> Any:
            if content_type not in self.handlers:
                self.handlers[content_type] = []

            _handler = eventflux.handler.Handler(func=func)

            self.handlers[content_type].append(
                {
                    "handler": _handler,
                    "jsonata_expr": compiled_jsonata_expr,
                }
            )
            return func

        return decorator

    async def route_if_match(
        self,
        event: eventflux.event.Event,
        content_type: typing.Literal["application/json"] = "application/json",
    ):
        if content_type not in self.handlers:
            raise ValueError("Invalid content-type detected!")

        await asyncio.gather(
            *[
                handler["handler"].handle(event=event.payload)
                for handler in self.handlers[content_type]
                if handler["jsonata_expr"].evaluate(event.payload)
            ]
        )
