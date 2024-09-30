import logging

import eventflux
import eventflux.router

app = eventflux.App(identifier="user-service", log_level=logging.INFO)

user_event_router = eventflux.router.GenericEventRouter()

kafka_subscriber = eventflux.KafkaCloudEventSubscriber(
    bootstrap_servers="localhost:9092",
    topics=["example"],
    group_id="ms-user-service",
)


# @user_event_router.on_event(
#     content_type="application/json", jsonata_expr='type = "example.user.created"'
# )
# def user_created_handler(event: eventflux.Event) -> None:
#     print(event)


@user_event_router.on_event(
    content_type="application/json", type="example.user.deleted"
)
def user_deleted(event: eventflux.Event) -> None:
    print(event)


app.mount_subscriber(subscriber=kafka_subscriber)
app.mount_router(router=user_event_router)
app.run()
