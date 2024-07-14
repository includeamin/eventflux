import abc

import cloudevents.pydantic.v2.event


class BaseEvent(abc.ABC):
    pass


class CloudEvent(cloudevents.pydantic.v2.CloudEvent):
    pass
