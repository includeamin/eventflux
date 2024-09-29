from unittest.mock import MagicMock

import pytest

import eventflux.event
from eventflux.handler import Handler


def test_handler_initialization_with_valid_sync_function():
    """
    Test that the handler is initialized correctly with a valid synchronous function.
    """

    def mock_func(event):
        return "test"

    handler = Handler(mock_func)

    # Ensure that the function is stored
    assert handler.func == mock_func

    # Ensure that _awaitable is set to False for sync functions
    assert not handler._awaitable


def test_handler_initialization_with_valid_async_function():
    """
    Test that the handler is initialized correctly with a valid asynchronous function.
    """

    async def mock_func(event):
        return "test"

    handler = Handler(mock_func)

    # Ensure that the function is stored
    assert handler.func == mock_func

    # Ensure that _awaitable is set to True for async functions
    assert handler._awaitable


def test_handler_raises_error_if_event_parameter_is_missing():
    """
    Test that ValueError is raised if the function does not accept an 'event' parameter.
    """

    def mock_func_without_event():
        return "test"

    with pytest.raises(ValueError, match="Missing 'event' parameter"):
        Handler(mock_func_without_event)


@pytest.mark.asyncio
async def test_handler_handle_sync_function():
    """
    Test that the handler correctly invokes a synchronous function.
    """

    def mock_func(event):
        return "handled"

    mock_event = eventflux.event.Event(payload={"test": "data"})
    handler = Handler(mock_func)

    result = await handler.handle(mock_event)

    # Ensure the sync function was called and returned the expected value
    assert result == "handled"


@pytest.mark.asyncio
async def test_handler_handle_async_function():
    """
    Test that the handler correctly awaits an asynchronous function.
    """

    async def mock_func(event):
        return "handled"

    mock_event = eventflux.event.Event(payload={"test": "data"})
    handler = Handler(mock_func)

    result = await handler.handle(mock_event)

    # Ensure the async function was awaited and returned the expected value
    assert result == "handled"


@pytest.mark.asyncio
async def test_handler_calls_event_with_event_argument():
    """
    Test that the handler passes the event object to the function correctly.
    """
    mock = MagicMock(return_value="handled")

    def mock_func(event):
        mock(event=event)

    mock_event = eventflux.event.Event(payload={"test": "data"})
    handler = Handler(mock_func)

    await handler.handle(mock_event)

    # Ensure the function was called with the correct event argument
    mock.assert_called_once_with(event=mock_event)
