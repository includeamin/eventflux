import asyncio
import logging
import signal
import time
import uuid

import structlog

import eventflux.logger
import eventflux.router
import eventflux.subscribers.base


class App:
    """
    Application class that manages event routers and subscribers, processes events asynchronously, and
    ensures graceful shutdown with ongoing task monitoring.
    """

    def __init__(
        self, identifier: str | None = None, log_level: int = logging.INFO
    ) -> None:
        """
        Initializes the application with a unique identifier, log level, and empty lists for routers and subscribers.

        Args:
            identifier (str | None): Unique identifier for the application instance (optional).
            log_level (int): Logging level (default is INFO).
        """
        self.identifier = identifier if identifier else str(uuid.uuid4())
        self.routers: list[eventflux.router.GenericEventRouter] = []
        self.subscribers: list[eventflux.subscribers.base.SubscriberAbstractClass] = []
        self._in_progress_tasks: dict[int, asyncio.Task] = {}
        self._must_exit = False

        # Set up logger
        eventflux.logger.setup()
        logging.basicConfig(level=log_level)
        self.logger = structlog.get_logger()

    def mount_router(self, router: eventflux.router.GenericEventRouter) -> None:
        """
        Adds a router to the list of event routers to process incoming events.

        Args:
            router (GenericEventRouter): The router to be added.
        """
        self.routers.append(router)

    def mount_subscriber(
        self, subscriber: eventflux.subscribers.base.SubscriberAbstractClass
    ) -> None:
        """
        Adds a subscriber to the list of event subscribers that listen for events.

        Args:
            subscriber (SubscriberAbstractClass): The subscriber to be added.
        """
        self.subscribers.append(subscriber)

    async def _process_events(self, queue: asyncio.Queue) -> None:
        """
        Asynchronously processes events from the queue and delegates them to routers for handling.

        Args:
            queue (asyncio.Queue): The queue holding events to be processed.
        """
        self.logger.info("Start processing events")
        while not self._must_exit:
            if queue.empty():
                self.logger.debug("Empty queue detected, waiting for input")
                await asyncio.sleep(0.01)
                continue
            event = await queue.get()
            task = asyncio.create_task(self.handle(event=event))
            self._in_progress_tasks[id(event)] = task
            await asyncio.sleep(0.01)

        # Log when the processing stops
        self.logger.info(
            "Worker has been stopped",
            in_progress_events_count=len(self._in_progress_tasks),
        )

    async def _start_listening(
        self,
        queue: asyncio.Queue,
        subscriber: eventflux.subscribers.base.SubscriberAbstractClass,
    ) -> None:
        """
        Asynchronously listens to events from the subscriber and adds them to the queue for processing.

        Args:
            queue (asyncio.Queue): The queue to place incoming events.
            subscriber (SubscriberAbstractClass): The subscriber that emits events.
        """
        self.logger.info("Starting listeners", listeners_count=len(self.subscribers))
        async for event in subscriber.listening():
            if self._must_exit:
                self.logger.info("Stop listening")
                break
            await queue.put(event)
            self.logger.debug(
                "Task added to queue",
                total_in_progress_tasks=len(self._in_progress_tasks),
            )
            await asyncio.sleep(0.01)

    async def handle(self, event: eventflux.event.Event) -> None:
        """
        Routes the event to all registered routers and processes it.

        Args:
            event (Event): The event to handle.
        """
        start_time = time.time()
        tasks = [router.route_if_match(event=event) for router in self.routers]
        await asyncio.gather(*tasks)
        self.logger.debug(
            "Event processed",
            duration=(time.time() - start_time) * 1000,  # Convert to milliseconds
        )
        self._in_progress_tasks.pop(id(event))

    def run(self) -> None:
        """
        Runs the application by starting the event loop and initiating event processing.
        """
        asyncio.run(self.async_app())

    def finish(self) -> None:
        """
        Signals the application to stop and exit gracefully by setting the `_must_exit` flag.
        """
        self._must_exit = True

    async def _monitor_in_progress_tasks(self) -> None:
        """
        Monitors ongoing tasks and ensures all tasks complete before the application exits.
        """
        while not self._must_exit:
            await asyncio.sleep(0.1)
        self.logger.info(
            "Waiting for all tasks to finish",
            total_in_progress_tasks=len(self._in_progress_tasks),
        )
        await asyncio.gather(*list(self._in_progress_tasks.values()))
        self.logger.info("All tasks finished, shutting down")

    async def async_app(self) -> None:
        """
        Asynchronous entry point for the application, setting up signal handlers and starting event processing.
        """
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, self.finish)
        queue: asyncio.Queue = asyncio.Queue()

        # Gather async tasks: event processing, listening, and task monitoring
        await asyncio.gather(
            self._process_events(queue=queue),
            self._start_listening(subscriber=self.subscribers[0], queue=queue),
            self._monitor_in_progress_tasks(),
        )
