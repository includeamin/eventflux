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
    """Test that a handler is correctly registered with the on_event method using a JSONata expression."""
    mock_func = AsyncMock()

    async def mock_handler(event):
        await mock_func(event=event)

    json_expr = "type = 'test'"
    handler_instance = MockHandler.return_value

    # Register the event handler with a JSONata expression
    event_router.on_event(jsonata_expr=json_expr)(mock_handler)

    # Check that the handler was added to the correct content type
    assert "application/json" in event_router.handlers
    handlers_list = event_router.handlers["application/json"]
    assert len(handlers_list) == 1

    # Check that the handler and compiled JSONata expression are stored
    registered_handler = handlers_list[0]
    assert registered_handler["handler"] == handler_instance
    assert isinstance(registered_handler["jsonata_expr"], jsonata.Jsonata)


def test_on_event_raises_value_error_if_no_jsonata_expr(event_router):
    """Test that ValueError is raised if no JSONata expression is provided when registering a handler."""
    with pytest.raises(ValueError, match="A JSONata expression is required"):
        event_router.on_event(jsonata_expr=None)


@pytest.mark.asyncio
async def test_on_event_registers_multiple_handlers(event_router):
    """Test that multiple handlers can be registered for the same JSONata expression and content type."""
    mock_func1 = AsyncMock()
    mock_func2 = AsyncMock()

    @event_router.on_event(
        content_type="application/json", jsonata_expr='type = "example"'
    )
    async def handler(event: dict) -> None:
        await mock_func1(event=event)

    @event_router.on_event(
        content_type="application/json", jsonata_expr='type = "example"'
    )
    async def handler2(event) -> None:
        await mock_func2(event=event)

    await event_router.route_if_match(
        event=eventflux.event.Event(payload={"type": "example"})
    )

    mock_func1.assert_awaited_once_with(event={"type": "example"})
    mock_func2.assert_awaited_once_with(event={"type": "example"})


@pytest.mark.asyncio
async def test_route_if_match_no_match(event_router):
    """Test that no handlers are called if the event does not match any registered JSONata expressions."""
    mock = AsyncMock()

    @event_router.on_event(
        content_type="application/json", jsonata_expr='type = "example"'
    )
    async def handler(event) -> None:
        await mock(event=event)

    await event_router.route_if_match(
        event=eventflux.event.Event(payload={"type": "examples"})
    )

    mock.assert_not_called()


@pytest.mark.asyncio
async def test_route_if_match_raises_error_for_invalid_content_type(event_router):
    """Test that route_if_match raises ValueError for an invalid content type."""
    event = eventflux.event.Event(payload={"type": "test"})

    with pytest.raises(
        ValueError, match="Invalid content type 'invalid/type' detected!"
    ):
        await event_router.route_if_match(event, content_type="invalid/type")


@pytest.mark.asyncio
async def test_route_if_match_executes_multiple_matching_handlers_using_jsonata_expr(
    event_router,
):
    """Test that multiple matching handlers for the same JSONata expression are executed concurrently."""
    mock = AsyncMock()

    @event_router.on_event(
        content_type="application/json", jsonata_expr='type = "example"'
    )
    async def handler(event) -> None:
        await mock(event=event)

    await event_router.route_if_match(
        event=eventflux.event.Event(payload={"type": "example"})
    )

    mock.assert_awaited_once_with(event={"type": "example"})


@pytest.mark.asyncio
async def test_route_if_match_executes_multiple_matching_handlers_using_filters(
    event_router,
):
    """Test that multiple matching handlers are executed concurrently based on filters."""
    mock = AsyncMock()

    @event_router.on_event(content_type="application/json", type="example")
    async def handler(event: dict) -> None:
        await mock(event=event)

    await event_router.route_if_match(
        event=eventflux.event.Event(payload={"type": "example"})
    )

    mock.assert_awaited_once_with(event={"type": "example"})


@pytest.mark.asyncio
async def test_route_if_match_executes_multiple_matching_handlers_using_nested_filters(
    event_router,
):
    """Test that multiple matching handlers are executed concurrently using nested filters."""
    mock = AsyncMock()

    payload = {"type": "user.location.registered", "data": {"country_code": "DE"}}

    @event_router.on_event(content_type="application/json", data={"country_code": "DE"})
    async def handler(event: dict) -> None:
        await mock(event=event)

    await event_router.route_if_match(event=eventflux.event.Event(payload=payload))

    mock.assert_awaited_once_with(event=payload)


@pytest.mark.asyncio
async def test_route_if_match_executes_multiple_matching_handlers_using_super_nested_filters(
    event_router,
):
    """Test that multiple matching handlers are executed concurrently using super nested filters."""

    mock = AsyncMock()

    payload = {
        "type": "user.location.registered",
        "data": {"location": {"country_code": "DE", "alt": 0, "lat": 0, "lon": 0}},
    }

    @event_router.on_event(
        content_type="application/json", data={"location": {"country_code": "DE"}}
    )
    async def handler(event: dict) -> None:
        await mock(event=event)

    await event_router.route_if_match(event=eventflux.event.Event(payload=payload))

    mock.assert_awaited_once_with(event=payload)


@pytest.mark.asyncio
async def test_route_if_match_executes_multiple_matching_handlers_operator_based_gt(
    event_router,
):
    """Test that multiple matching handlers are executed concurrently using super nested filters."""

    mock = AsyncMock()

    payload = {
        "type": "user.registered",
        "data": {"age": 30},
    }

    payload2 = {
        "type": "user.registered",
        "data": {"age": 20},
    }

    @event_router.on_event(
        content_type="application/json",
        type="user.registered",
        data={"age": {"$gt": 20}},
    )
    async def handler(event: dict) -> None:
        await mock(event=event)

    await event_router.route_if_match(event=eventflux.event.Event(payload=payload))
    await event_router.route_if_match(event=eventflux.event.Event(payload=payload2))

    mock.assert_awaited_once_with(event=payload)
