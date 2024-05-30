import asyncio
import random
import time

import eventflux

app = eventflux.App(identifier="user-service")

user_event_router = eventflux.Router()

kafka_subscriber = eventflux.KafkaSubscriber(
    bootstrap_servers="localhost:9092",
    topics=["magicscout"],
    group_id="ms-user-service",
)


@user_event_router.on_event(type="magicscout.user.created")
def user_created_handler(event: eventflux.CloudEvent):
    print(event.subject, event.type)


@user_event_router.on_event(type="magicscout.user.updated")
async def user_updated_handler(event: eventflux.CloudEvent):
    print(event.subject, event.type)
    await asyncio.sleep(random.randint(1, 10))


app.mount_subscriber(subscriber=kafka_subscriber)
app.mount_router(router=user_event_router)
app.run()
