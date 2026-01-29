"""
Update dispatcher with queue and concurrency control
"""

import asyncio

from ymbot_async.api.client import ApiClient
from ymbot_async.api.schemas import Update
from ymbot_async.config import BotConfig
from ymbot_async.dispatcher.handlers import Handler
from ymbot_async.logging import LoggerProtocol, get_logger

logger: LoggerProtocol = get_logger(__name__)


class Dispatcher:
    """
    Update dispatcher with bounded queue and concurrency control.

    Features:
    - Bounded queue for updates (drops updates when full)
    - Concurrency limit for handlers
    - Sequential update processing (offset is saved only after handler completes)
    - Safe shutdown with graceful draining
    """

    def __init__(
        self,
        api_client: ApiClient,
        config: BotConfig,
    ):
        """
        Initialize dispatcher.

        Args:
            api_client: API client instance
            config: Bot configuration
        """
        self.api_client = api_client
        self.config = config
        self.handlers: list[Handler] = []

        # Create bounded queue (maxsize=0 means unbounded, but we use config value)
        self._update_queue: asyncio.Queue[Update | None] = asyncio.Queue(
            maxsize=config.queue_maxsize
        )

        # Semaphore for concurrency control
        self._concurrency_semaphore = asyncio.Semaphore(config.concurrency)

        # Track running tasks
        self._running_tasks: set[asyncio.Task] = set()

        # Event to signal shutdown
        self._shutdown_event = asyncio.Event()

        # Track if dispatcher is stopped
        self._stopped = False

        logger.info(
            "Dispatcher initialized",
            queue_maxsize=config.queue_maxsize,
            concurrency=config.concurrency,
        )

    def register_handler(self, handler: Handler) -> None:
        """
        Register a handler.

        Args:
            handler: Handler to register
        """
        print(
            f"DEBUG dispatcher.register_handler: appending handler, total before={len(self.handlers)}"
        )
        self.handlers.append(handler)
        print(f"DEBUG dispatcher.register_handler: total after={len(self.handlers)}")
        logger.debug(
            "Handler registered",
            handler_type=type(handler).__name__,
            total_handlers=len(self.handlers),
        )

    async def feed_update(self, update: Update) -> bool:
        """
        Feed an update to the dispatcher queue.

        Args:
            update: Update to feed

        Returns:
            True if update was added to queue, False if queue is full (dropped)
        """
        if self._stopped:
            logger.warning("Dropping update: dispatcher is stopped")
            return False

        try:
            self._update_queue.put_nowait(update)
            logger.debug(
                "Update added to queue",
                update_id=update.update_id,
                queue_size=self._update_queue.qsize(),
            )
            return True
        except asyncio.QueueFull:
            logger.warning(
                "Dropping update: queue is full",
                update_id=update.update_id,
                queue_maxsize=self.config.queue_maxsize,
            )
            return False

    async def stop(self) -> None:
        """
        Stop the dispatcher gracefully.

        Waits for all running handlers to complete, then signals shutdown.
        """
        if self._stopped:
            return

        logger.info("Stopping dispatcher")
        self._stopped = True

        # Wait for all running tasks
        if self._running_tasks:
            logger.info(
                "Waiting for running handlers",
                count=len(self._running_tasks),
            )
            await asyncio.gather(*self._running_tasks, return_exceptions=True)

        # Signal shutdown to worker tasks
        await self._update_queue.put(None)
        self._shutdown_event.set()
        logger.info("Dispatcher stopped")

    async def _process_update(self, update: Update) -> None:
        """
        Process a single update with concurrency control.

        Args:
            update: Update to process
        """
        async with self._concurrency_semaphore:
            try:
                logger.debug(
                    "Processing update",
                    update_id=update.update_id,
                )

                # Find and execute matching handler
                for handler in self.handlers:
                    if handler.check(update):
                        await handler.handle(update)
                        logger.debug(
                            "Handler executed",
                            update_id=update.update_id,
                            handler_type=type(handler).__name__,
                        )
                        break
                else:
                    logger.debug(
                        "No handler matched",
                        update_id=update.update_id,
                    )

            except Exception as e:
                logger.exception(
                    "Handler error",
                    update_id=update.update_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                # Continue processing other updates

    def _create_worker_task(self) -> asyncio.Task:
        """
        Create a worker task to process updates.

        Returns:
            Worker task
        """

        async def worker() -> None:
            """Worker coroutine that processes updates from queue"""
            while not self._shutdown_event.is_set():
                try:
                    # Get update from queue with timeout
                    update = await asyncio.wait_for(
                        self._update_queue.get(),
                        timeout=1.0,
                    )

                    # Check for shutdown signal
                    if update is None:
                        break

                    # Process update
                    task = asyncio.create_task(self._process_update(update))
                    self._running_tasks.add(task)
                    task.add_done_callback(self._running_tasks.discard)

                except TimeoutError:
                    # Timeout is expected - check shutdown and continue
                    continue
                except Exception as e:
                    logger.exception(
                        "Worker error",
                        error_type=type(e).__name__,
                        error_message=str(e),
                    )

        return asyncio.create_task(worker())

    async def run(self) -> None:
        """
        Run the dispatcher.

        Starts worker tasks and processes updates until stop() is called.
        """
        if self._stopped:
            raise RuntimeError("Cannot start stopped dispatcher")

        logger.info("Starting dispatcher")

        # Start worker tasks (one per concurrency limit)
        worker_tasks = [self._create_worker_task() for _ in range(self.config.concurrency)]

        # Wait for shutdown
        await self._shutdown_event.wait()

        # Wait for all workers to finish
        await asyncio.gather(*worker_tasks, return_exceptions=True)

        logger.info("Dispatcher finished")
