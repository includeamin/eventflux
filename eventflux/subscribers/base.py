import abc
import typing

import eventflux.event


class SubscriberAbstractClass(abc.ABC):
    @abc.abstractmethod
    def listening(self) -> typing.AsyncIterator[eventflux.event.CloudEvent]:
        raise NotImplementedError
