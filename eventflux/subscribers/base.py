import typing
import eventflux.event
import abc


class SubscriberAbstractClass(abc.ABC):
    @abc.abstractmethod
    async def listening(self) -> typing.AsyncIterator[eventflux.event.CloudEvent]:
        raise NotImplementedError
