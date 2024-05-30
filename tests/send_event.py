import datetime
import time
import json
import uuid

from kafka import KafkaProducer
from cloudevents.pydantic.v2 import CloudEvent

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v.json()).encode("utf-8"),
)
action = "created"
count = 0
while True:
    event = CloudEvent(
        subject=f"magicscout:user:{uuid.uuid4()}",
        data={"created_at": datetime.datetime.now().timestamp()},
        type=f"magicscout.user.{action}",
        source="magicscout.service.user",
    )
    if action == "created":
        action = "updated"
    else:
        action = "created"

    time.sleep(1)
    res = producer.send(topic="magicscout", value=event)
    producer.flush()
    print(res.is_done, count)
    count += 1
