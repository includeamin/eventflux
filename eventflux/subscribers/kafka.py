import typing

import orjson
from kafka import KafkaConsumer

import eventflux.event
import eventflux.subscribers.base

SERIALIZER_TYPE = typing.Callable[[typing.Any], eventflux.event.CloudEvent]


class KafkaCloudEventSubscriber(eventflux.subscribers.base.SubscriberAbstractClass):
    def __init__(
        self,
        bootstrap_servers: typing.Union[str, list[str]],
        group_id: str,
        topics: list[str] | None = None,
        pattern: str | None = None,
        event_serializer: SERIALIZER_TYPE | None = None,
        **kafka_kwargs,
    ):
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda x: orjson.loads(x.decode("utf-8")),
            **kafka_kwargs,
        )
        self.topics = topics
        self.pattern = pattern
        self.event_serializer = event_serializer

    def set_topics(self, topics: list[str]) -> None:
        self.topics = topics

    async def listening(self) -> typing.AsyncIterator[eventflux.event.CloudEvent]:
        self.consumer.subscribe(topics=self.topics, pattern=self.pattern)
        for msg in self.consumer:
            if self.event_serializer is not None:
                yield self.event_serializer(msg.value)
            else:
                yield eventflux.event.CloudEvent(**orjson.loads(msg.value))
