"""
Long polling implementation with backoff
"""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable

from ymbot_async.api.client import ApiClient
from ymbot_async.api.schemas import Update
from ymbot_async.config import BotConfig
from ymbot_async.logging import LoggerProtocol, get_logger

logger: LoggerProtocol = get_logger(__name__)


class Poller:
    """
    Long polling implementation with exponential backoff.

    Features:
    - Bounded delay on consecutive empty responses
    - Graceful shutdown support
    - Error handling and recovery
    """

    def __init__(
        self,
        api_client: ApiClient,
        config: BotConfig,
    ):
        """
        Initialize poller.

        Args:
            api_client: API client instance
            config: Bot configuration
        """
        self.api_client = api_client
        self.config = config
        self._shutdown_event = asyncio.Event()
        self._polling_task: asyncio.Task | None = None
        self._empty_response_count = 0

        logger.info("Poller initialized")

    async def _calculate_backoff(self) -> float:
        """
        Calculate backoff delay based on consecutive empty responses.

        Returns:
            Backoff delay in seconds
        """
        backoff = self.config.polling_timeout * (
            (1.0 / self.config.polling_backoff) ** self._empty_response_count
        )
        return min(backoff, self.config.polling_max_backoff)

    async def _fetch_updates(
        self,
        offset: int,
    ) -> list[Update]:
        """
        Fetch updates from API.

        Args:
            offset: Current offset

        Returns:
            List of updates

        Raises:
            Exception: If API request fails (retryable)
        """
        response = await self.api_client.get_updates(
            offset=offset,
            limit=self.config.polling_limit,
            timeout=self.config.polling_timeout,
        )
        return response.updates

    async def _polling_loop(
        self,
        offset_getter: Callable[[], Awaitable[int]],
        update_callback: Callable[[Update], Awaitable[None]],
    ) -> None:
        """
        Main polling loop.

        Args:
            offset_getter: Async function to get current offset
            update_callback: Async function to process each update
        """
        logger.info("Starting polling loop")

        while not self._shutdown_event.is_set():
            try:
                # Get current offset
                offset = await offset_getter()

                # Fetch updates
                updates = await self._fetch_updates(offset)

                # Check for empty response
                if not updates:
                    self._empty_response_count += 1
                    backoff = await self._calculate_backoff()
                    logger.debug(
                        "No updates received",
                        empty_count=self._empty_response_count,
                        backoff=round(backoff, 2),
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Reset empty response counter
                if self._empty_response_count > 0:
                    logger.debug(
                        "Received updates after empty responses",
                        empty_count=self._empty_response_count,
                    )
                self._empty_response_count = 0

                # Process updates
                for update in updates:
                    if self._shutdown_event.is_set():
                        break

                    logger.debug(
                        "Received update",
                        update_id=update.update_id,
                    )

                    # Process update via callback
                    await update_callback(update)

            except asyncio.CancelledError:
                logger.info("Polling cancelled")
                break
            except Exception as e:
                logger.exception(
                    "Polling error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                # Wait before retrying
                await asyncio.sleep(self.config.polling_timeout)

        logger.info("Polling loop finished")

    async def start(
        self,
        offset_getter: Callable[[], Awaitable[int]],
        update_callback: Callable[[Update], Awaitable[None]],
    ) -> None:
        """
        Start polling.

        Args:
            offset_getter: Async function to get current offset
            update_callback: Async function to process each update
        """
        if self._polling_task and not self._polling_task.done():
            raise RuntimeError("Poller is already running")

        self._shutdown_event.clear()
        self._polling_task = asyncio.create_task(
            self._polling_loop(
                offset_getter=offset_getter,
                update_callback=update_callback,
            )
        )
        logger.info("Poller started")

    async def stop(self) -> None:
        """
        Stop polling gracefully.

        Waits for the current polling request to complete.
        """
        if not self._polling_task:
            return

        logger.info("Stopping poller")
        self._shutdown_event.set()

        # Wait for polling task to finish
        try:
            await asyncio.wait_for(
                self._polling_task,
                timeout=self.config.polling_timeout + 5.0,
            )
        except TimeoutError:
            logger.warning("Poller stop timed out, cancelling task")
            self._polling_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._polling_task

        # Clear all references to help garbage collection
        self._polling_task = None
        self._empty_response_count = 0
        logger.info("Poller stopped")
