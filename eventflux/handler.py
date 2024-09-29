import inspect
import typing

import eventflux.event


class Handler:
    """
    A handler class that wraps a function and determines whether it is synchronous or asynchronous.
    Ensures the function has an 'event' parameter and handles both types of functions accordingly.
    """

    def __init__(self, func: typing.Callable) -> None:
        """
        Initializes the handler with the provided function and analyzes its signature.

        Args:
            func (Callable): The function to be wrapped by the handler.

        Raises:
            ValueError: If the function does not accept an 'event' parameter.
        """
        self.func = func
        self._awaitable = False
        self._analyze_handler_func()

    def _analyze_handler_func(self) -> None:
        """
        Analyzes the provided function to ensure it has an 'event' parameter
        and determines whether it is a coroutine (async function).
        """
        signature = inspect.signature(self.func)

        # Ensure the function has an 'event' parameter
        if "event" not in signature.parameters:
            raise ValueError(
                f"Missing 'event' parameter in handler '{self.func.__name__}'"
            )

        # Check if the function is a coroutine (async)
        self._awaitable = inspect.iscoroutinefunction(self.func)

    async def handle(self, event: eventflux.event.Event) -> typing.Any:
        """
        Invokes the handler's function, handling both synchronous and asynchronous functions.

        Args:
            event (Event): The event object to pass to the function.

        Returns:
            Any: The result of the function call, or the awaited result if the function is async.
        """
        if self._awaitable:
            # Await the function if it's an async function
            return await self.func(event=event)
        # Call the function synchronously if not async
        return self.func(event=event)
