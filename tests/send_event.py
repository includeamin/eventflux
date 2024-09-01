import datetime
import json
import random
import time
import uuid

from cloudevents.pydantic.v2 import CloudEvent
from kafka import KafkaProducer

producer = KafkaProducer(
    # bootstrap_servers="localhost:9092",
    bootstrap_servers="192.168.178.23:9092",
    value_serializer=lambda v: v.model_dump_json().encode("utf-8"),
)
action = "created"
count = 0
available_actions = ["created", "registered", "updated", "deleted"]
while True:
    event = CloudEvent(
        subject=f"magicscout:user:{uuid.uuid4()}",
        data={"created_at": datetime.datetime.now().timestamp()},
        type=f"platform.user.{available_actions[random.randint(0,3)]}",  # noqa: S311
        # type=f"platform.user.created",  # noqa: S311
        source="magicscout.service.user",
    )

    time.sleep(1)
    res = producer.send(topic="platform.user", value=event)
    # print(event.model_dump_json())
    producer.flush()
    print(res.is_done, count)
    count += 1
