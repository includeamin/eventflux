from unittest.mock import AsyncMock, patch

import jsonata
import pytest

import eventflux.event
import eventflux.handler
from eventflux.router import GenericEventRouter


@pytest.fixture
def event_router():
    """Fixture to create a new GenericEventRouter instance for each test."""
    return GenericEventRouter()


@patch("eventflux.handler.Handler")
def test_on_event_registers_handler(MockHandler, event_router):
    """Test that the on_event method correctly registers a handler."""
    mock_func = AsyncMock()

    async def mock_hanler(event):
        await mock_func(event=event)

    json_expr = "type = 'test'"
    handler_instance = MockHandler.return_value

    # Register the event handler with a JSONata expression
    event_router.on_event(jsonata_expr=json_expr)(mock_hanler)

    # Check that the handler was added to the correct content type
    assert "application/json" in event_router.handlers
    handlers_list = event_router.handlers["application/json"]
    assert len(handlers_list) == 1

    # Check that the handler and compiled JSONata expression are stored
    registered_handler = handlers_list[0]
    assert registered_handler["handler"] == handler_instance
    assert isinstance(registered_handler["jsonata_expr"], jsonata.Jsonata)


def test_on_event_raises_value_error_if_no_jsonata_expr(event_router):
    """Test that ValueError is raised if no JSONata expression is provided."""
    with pytest.raises(ValueError, match="A JSONata expression is required"):
        event_router.on_event(jsonata_expr=None)


@patch("eventflux.handler.Handler")
def test_on_event_registers_multiple_handlers(MockHandler, event_router):
    """Test that multiple handlers can be registered for the same content type."""
    mock_func1 = AsyncMock()

    async def mock_1_hanler(event):
        await mock_func1(event=event)

    mock_func2 = AsyncMock()

    async def mock_2_hanler(event):
        await mock_func2(event=event)

    # Register multiple handlers
    event_router.on_event(jsonata_expr="type = 'test'")(mock_1_hanler)
    event_router.on_event(jsonata_expr="type = 'test2'")(mock_2_hanler)

    # Check that both handlers are registered
    handlers_list = event_router.handlers["application/json"]
    assert len(handlers_list) == 2


@pytest.mark.asyncio
async def test_route_if_match_no_match(event_router):
    """Test that no handlers are called if no JSONata expression matches the event."""
    mock_func = AsyncMock()

    async def mock_hanler(event):
        await mock_func(event=event)

    event_router.on_event(jsonata_expr="type = 'test'")(mock_hanler)

    # Create an event that doesn't match the JSONata expression
    event = eventflux.event.Event(payload={"type": "non_matching_event"})

    # Patch the JSONata evaluate method to return False
    with patch("jsonata.Jsonata.evaluate", return_value=False):
        await event_router.route_if_match(event)

    # Ensure that the handler was not called
    mock_func.assert_not_called()


@pytest.mark.asyncio
async def test_route_if_match_executes_matching_handler(event_router):
    """Test that the handler is executed if the JSONata expression matches the event."""
    mock_func = AsyncMock()

    async def mock_hanler(event):
        await mock_func(event=event)

    event_router.on_event(jsonata_expr="type = 'test'")(mock_hanler)

    # Create an event that matches the JSONata expression
    event = eventflux.event.Event(payload={"type": "test"})

    # Patch the JSONata evaluate method to return True
    with patch("jsonata.Jsonata.evaluate", return_value=True):
        await event_router.route_if_match(event)

    # Ensure that the handler was called with the correct event payload
    mock_func.assert_awaited_once_with(event=event.payload)


@pytest.mark.asyncio
async def test_route_if_match_raises_error_for_invalid_content_type(event_router):
    """Test that route_if_match raises ValueError for an invalid content type."""
    event = eventflux.event.Event(payload={"type": "test"})

    with pytest.raises(
        ValueError, match="Invalid content type 'invalid/type' detected!"
    ):
        await event_router.route_if_match(event, content_type="invalid/type")


@pytest.mark.asyncio
async def test_route_if_match_executes_multiple_matching_handlers(event_router):
    """Test that multiple matching handlers are executed concurrently."""
    mock_func1 = AsyncMock()

    async def mock_1_hanler(event):
        await mock_func1(event=event)

    mock_func2 = AsyncMock()

    async def mock_2_hanler(event):
        await mock_func2(event=event)

    # Register two handlers with different JSONata expressions
    event_router.on_event(jsonata_expr="type = 'test'")(mock_1_hanler)
    event_router.on_event(jsonata_expr="type = 'test'")(mock_2_hanler)

    # Create an event that matches both handlers
    event = eventflux.event.Event(payload={"type": "test"})

    # Patch the JSONata evaluate method to return True for both handlers
    with patch("jsonata.Jsonata.evaluate", return_value=True):
        await event_router.route_if_match(event)

    # Ensure that both handlers were called concurrently
    mock_func1.assert_awaited_once_with(event=event.payload)
    mock_func2.assert_awaited_once_with(event=event.payload)
