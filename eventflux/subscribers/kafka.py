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
        topics: list[str],
        pattern: str | None = None,
        event_serializer: SERIALIZER_TYPE | None = None,
        **kwargs
    ):
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda x: orjson.loads(x.decode("utf-8")),
            **kwargs
        )
        self.consumer.subscribe(topics=topics, pattern=pattern)
        self.event_serializer = event_serializer

    async def listening(self) -> typing.AsyncIterator[eventflux.event.CloudEvent]:
        for msg in self.consumer:
            if self.event_serializer is not None:
                yield self.event_serializer(msg.value)
            else:
                yield eventflux.event.CloudEvent(**orjson.loads(msg.value))
