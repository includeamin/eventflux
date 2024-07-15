import eventflux

app = eventflux.App(identifier="user-service")

user_event_router = eventflux.CloudEventRouter()

kafka_subscriber = eventflux.KafkaCloudEventSubscriber(
    bootstrap_servers="localhost:9092",
    topics=["magicscout"],
    group_id="ms-user-service",
)


@user_event_router.on_event(
    types=["magicscout.user.created", "magicscout.user.registered"]
)
def user_created_handler(event: eventflux.CloudEvent) -> None:
    print(event.subject, event.type)


@user_event_router.on_event(type="magicscout.user.updated")
async def user_updated_handler(event: eventflux.CloudEvent) -> None:
    print(event.subject, event.type)
    # await asyncio.sleep(5)


app.mount_subscriber(subscriber=kafka_subscriber)
app.mount_router(router=user_event_router)
app.run()
