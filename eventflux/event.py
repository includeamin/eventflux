import dataclasses
import uuid


@dataclasses.dataclass
class Event:
    payload: dict
    id: str = str(uuid.uuid4())
