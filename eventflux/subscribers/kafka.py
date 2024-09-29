import typing

import orjson
from kafka import KafkaConsumer

import eventflux.event
import eventflux.subscribers.base

SERIALIZER_TYPE = typing.Callable[[typing.Any], eventflux.event.Event]


class KafkaCloudEventSubscriber(eventflux.subscribers.base.SubscriberAbstractClass):
    """
    Kafka subscriber that listens to Kafka topics and yields events either as raw or serialized objects.
    Designed to integrate with the EventFlux framework by emitting events in the expected format.
    """

    def __init__(
        self,
        bootstrap_servers: typing.Union[str, list[str]],
        group_id: str,
        topics: list[str],
        pattern: str | None = None,
        event_serializer: SERIALIZER_TYPE | None = None,
        **kwargs
    ) -> None:
        """
        Initializes the KafkaCloudEventSubscriber with Kafka connection parameters and topic subscription.

        Args:
            bootstrap_servers (Union[str, list[str]]): Kafka bootstrap server(s).
            group_id (str): The consumer group ID.
            topics (list[str]): The list of Kafka topics to subscribe to.
            pattern (str | None): Regex pattern to match Kafka topics (optional).
            event_serializer (SERIALIZER_TYPE | None): A callable that serializes Kafka message values into EventFlux events (optional).
            kwargs: Additional keyword arguments for KafkaConsumer configuration.
        """
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda x: orjson.loads(x.decode("utf-8")),
            **kwargs
        )
        # Subscribe to the provided topics or pattern
        self.consumer.subscribe(topics=topics, pattern=pattern)
        self.event_serializer = event_serializer

    async def listening(self) -> typing.AsyncIterator[eventflux.event.Event]:
        """
        Asynchronously listens to Kafka messages and yields deserialized events.
        If an event serializer is provided, it is used to convert Kafka messages to EventFlux events.

        Yields:
            AsyncIterator[Event]: An async iterator of EventFlux events.

        """
        for msg in self.consumer:
            # Use custom serializer if provided, otherwise create EventFlux event with the deserialized value
            if self.event_serializer:
                yield self.event_serializer(msg.value)
            else:
                yield eventflux.event.Event(payload=orjson.loads(msg.value))
