import asyncio
import typing
from collections.abc import Callable
from typing import Any

import jsonata

import eventflux.event
import eventflux.handler


class GenericEventRouter:
    """
    A generic event router that allows the registration of event handlers with filters based on JSONata expressions.
    Routes incoming events to the appropriate handler(s) if they match the corresponding filter.
    """

    def __init__(self) -> None:
        """
        Initializes the GenericEventRouter with an empty dictionary to hold handlers for each content type.
        """
        self.handlers: dict[str, list[dict[str, Any]]] = {}

    def on_event(
        self,
        content_type: typing.Literal["application/json"] = "application/json",
        jsonata_expr: str | None = None,
    ) -> Callable[[Callable[..., Any]], Any]:
        """
        Registers an event handler for a specific content type with a filter defined using a JSONata expression.

        Args:
            content_type (Literal): The content type of the event (default is "application/json").
            jsonata_expr (str): A JSONata expression to filter events.

        Returns:
            Callable: A decorator that registers the handler.

        Raises:
            ValueError: If no JSONata expression is provided.
        """
        if not jsonata_expr:
            raise ValueError("A JSONata expression is required")

        # Pre-compile the JSONata expression for performance optimization
        compiled_jsonata_expr = jsonata.Jsonata(jsonata_expr)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            """
            A decorator to register the event handler with the pre-compiled JSONata expression.
            """
            if content_type not in self.handlers:
                self.handlers[content_type] = []

            # Create a handler wrapper from eventflux.handler
            _handler = eventflux.handler.Handler(func=func)

            # Register the handler and its corresponding JSONata expression
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
    ) -> None:
        """
        Routes an event to the appropriate handlers if their filters match the event's payload.

        Args:
            event (Event): The event object to be routed.
            content_type (Literal): The content type of the event (default is "application/json").

        Raises:
            ValueError: If the content type is not registered.
        """
        if content_type not in self.handlers:
            raise ValueError(f"Invalid content type '{content_type}' detected!")

        # Concurrently evaluate handlers whose filters match the event payload
        matching_tasks = [
            handler["handler"].handle(event=event.payload)
            for handler in self.handlers[content_type]
            if handler["jsonata_expr"].evaluate(event.payload)
        ]

        # If there are matching tasks, run them concurrently
        if matching_tasks:
            await asyncio.gather(*matching_tasks)
