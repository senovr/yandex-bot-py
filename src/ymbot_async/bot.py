"""
Main Bot class for Yandex Messenger Bot Async Client
"""

import asyncio
from typing import Any

from ymbot_async.api.client import ApiClient
from ymbot_async.config import BotConfig
from ymbot_async.dispatcher.dispatcher import Dispatcher
from ymbot_async.dispatcher.filters import Filter
from ymbot_async.dispatcher.handlers import Handler, MessageHandler
from ymbot_async.logging import get_logger, setup_logging, LoggerProtocol
from ymbot_async.runtime.offset_manager import OffsetManager
from ymbot_async.runtime.polling import Poller
from ymbot_async.transport.httpx_transport import HttpxTransport

logger: LoggerProtocol = get_logger(__name__)


class Bot:
    """
    Main bot class that orchestrates all components.
    
    Usage:
        ```python
        from ymbot_async import Bot, BotConfig
        
        config = BotConfig(token="your_token")
        
        bot = Bot(config)
        
        @bot.message_handler(commands=["start"])
        async def start_handler(update):
            await bot.api_client.send_message(
                chat_id=update.message.chat.id,
                text="Hello!",
            )
        
        await bot.run_polling()
        ```
    """

    def __init__(
        self,
        config: BotConfig,
    ):
        """
        Initialize bot.
        
        Args:
            config: Bot configuration
        """
        self.config = config

        # Setup logging
        setup_logging(
            level=config.log_level,
            format_type=config.log_format,
        )

        # Create components
        self._transport: HttpxTransport | None = None
        self.api_client: ApiClient | None = None
        self.dispatcher: Dispatcher | None = None
        self.offset_manager: OffsetManager | None = None
        self.poller: Poller | None = None

        logger.info(
            "Bot initialized",
            log_level=config.log_level,
            log_format=config.log_format,
        )

    async def __aenter__(self):
        """Enter async context and initialize components."""
        # Create transport
        self._transport = HttpxTransport(self.config)
        await self._transport.__aenter__()

        # Create API client
        self.api_client = ApiClient(self._transport)

        # Create offset manager
        self.offset_manager = OffsetManager(self.config)

        # Create dispatcher
        self.dispatcher = Dispatcher(self.api_client, self.config)

        # Create poller
        self.poller = Poller(self.api_client, self.config)

        logger.info("Bot components initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup components."""
        logger.info("Cleaning up bot components")

        # Stop poller if running
        if self.poller:
            await self.poller.stop()

        # Stop dispatcher if running
        if self.dispatcher:
            await self.dispatcher.stop()

        # Close transport
        if self._transport:
            await self._transport.__aexit__(exc_type, exc_val, exc_tb)

        logger.info("Bot cleanup complete")

    def message_handler(
        self,
        filters: Filter | None = None,
    ):
        """
        Decorator to register a message handler.
        
        Args:
            filters: Filter(s) to apply
            
        Returns:
            Decorator function
            
        Example:
            ```python
            @bot.message_handler(commands=["start"])
            async def start_handler(update):
                await bot.api_client.send_message(
                    chat_id=update.message.chat.id,
                    text="Hello!",
                )
            ```
        """

        def decorator(func):
            if not self.dispatcher:
                raise RuntimeError(
                    "Bot not initialized. Use 'async with' context manager."
                )

            handler = MessageHandler(callback=func, filters=filters)
            self.dispatcher.register_handler(handler)
            logger.debug(
                "Message handler registered",
                function_name=func.__name__,
            )
            return func

        return decorator

    async def _process_update(self, update: Any) -> None:
        """
        Process a single update.
        
        Feeds update to dispatcher and commits offset after processing.
        
        Args:
            update: Update to process
        """
        if not self.dispatcher or not self.offset_manager:
            raise RuntimeError("Bot not initialized")

        try:
            # Feed update to dispatcher
            added = await self.dispatcher.feed_update(update)

            if not added:
                # Update was dropped (queue full or stopped)
                logger.warning(
                    "Update not processed",
                    update_id=update.update_id,
                    reason="not added to queue",
                )
                return

            # Commit offset after successful processing
            # Note: In this simple implementation, we commit immediately
            # A more robust implementation would wait for handler completion
            await self.offset_manager.commit_offset(update.update_id)

        except Exception as e:
            logger.exception(
                "Error processing update",
                update_id=update.update_id,
                error_type=type(e).__name__,
                error_message=str(e),
            )

    async def run_polling(self) -> None:
        """
        Run the bot with long polling.
        
        This method blocks until stop() is called or an error occurs.
        
        Example:
            ```python
            async def main():
                async with Bot(config) as bot:
                    @bot.message_handler(commands=["start"])
                    async def start_handler(update):
                        await bot.api_client.send_message(
                            chat_id=update.message.chat.id,
                            text="Hello!",
                        )
                    
                    await bot.run_polling()
            
            asyncio.run(main())
            ```
        """
        if not self.poller or not self.offset_manager or not self.dispatcher:
            raise RuntimeError("Bot not initialized")

        logger.info("Starting bot with long polling")

        try:
            # Start dispatcher
            dispatcher_task = asyncio.create_task(self.dispatcher.run())

            # Start polling
            await self.poller.start(
                offset_getter=self.offset_manager.get_offset,
                update_callback=self._process_update,
            )

            # Wait for dispatcher to finish
            await dispatcher_task

        except asyncio.CancelledError:
            logger.info("Polling cancelled")
        except Exception as e:
            logger.exception(
                "Polling error",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise
        finally:
            logger.info("Bot stopped")

    async def stop(self) -> None:
        """
        Stop the bot gracefully.
        
        Waits for all running handlers and polling to complete.
        """
        logger.info("Stopping bot")

        if self.poller:
            await self.poller.stop()

        if self.dispatcher:
            await self.dispatcher.stop()

        logger.info("Bot stopped")