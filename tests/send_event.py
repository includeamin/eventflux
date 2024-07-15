import datetime
import json
import random
import time
import uuid

from cloudevents.pydantic.v2 import CloudEvent
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v.json()).encode("utf-8"),
)
action = "created"
count = 0
available_actions = ["created", "registered", "updated"]
while True:
    event = CloudEvent(
        subject=f"magicscout:user:{uuid.uuid4()}",
        data={"created_at": datetime.datetime.now().timestamp()},
        type=f"magicscout.user.{available_actions[random.randint(0,2)]}",  # noqa: S311
        source="magicscout.service.user",
    )

    time.sleep(1)
    res = producer.send(topic="magicscout", value=event)
    producer.flush()
    print(res.is_done, count)
    count += 1
