import typing

import eventflux.subscribers.base
import orjson
from kafka import KafkaConsumer
import eventflux.event


class KafkaSubscriber(eventflux.subscribers.base.SubscriberAbstractClass):
    def __init__(
        self,
        bootstrap_servers: typing.Union[str, list[str]],
        group_id: str,
        topics: list[str],
        pattern: str = None,
        **kwargs
    ):
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda x: orjson.loads(x.decode("utf-8")),
            **kwargs
        )
        self.consumer.subscribe(topics=topics, pattern=pattern)

    async def listening(self) -> typing.AsyncIterator[eventflux.event.CloudEvent]:
        for msg in self.consumer:
            yield eventflux.event.CloudEvent(**orjson.loads(msg.value))
