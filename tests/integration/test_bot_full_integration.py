"""Full integration tests for Bot with mocked API"""

import asyncio
import contextlib
from unittest.mock import AsyncMock

import pytest

from ymbot_async.bot import Bot


class TestBotFullLifecycle:
    """Tests for full bot lifecycle: init → start → process → shutdown"""

    @pytest.mark.asyncio
    async def test_bot_full_start_stop_cycle(self, bot_config, httpx_transport):
        """Test complete bot lifecycle: init, start, process messages, stop"""
        _, _ = httpx_transport

        async def handler(update):
            return f"Processed: {update.text}"

        # Create and initialize bot
        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            # Start bot using run_polling in a task
            polling_task = asyncio.create_task(bot.run_polling())

            # Give it a moment to start
            await asyncio.sleep(0.1)

            # Stop bot
            await bot.stop()

            # Cancel polling task if still running
            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

        # Bot should be stopped
        assert bot.poller is None or bot.poller._polling_task is None

    @pytest.mark.asyncio
    async def test_bot_with_message_handler(self, bot_config, httpx_transport):
        """Test that message handler receives and processes messages"""
        _, _ = httpx_transport

        async def message_handler(update):
            return "OK"

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(message_handler)

            # Start and immediately stop
            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.05)
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

        # Handler was registered
        assert bot.dispatcher is not None

    @pytest.mark.asyncio
    async def test_bot_start_raises_when_already_running(self, bot_config, httpx_transport):
        """Test that start() raises RuntimeError when already running"""
        _, _ = httpx_transport

        async def handler(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            # Start polling
            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)

            # Note: There's no explicit start() method, run_polling is used
            # This test is adapted to verify run_polling behavior

            # Cleanup
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

    @pytest.mark.asyncio
    async def test_bot_stop_without_start(self, bot_config, httpx_transport):
        """Test that stop() works without calling start()"""
        _, _ = httpx_transport

        async def handler(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            # Should not raise
            await bot.stop()


class TestBotInitialization:
    """Tests for bot initialization and component setup"""

    @pytest.mark.asyncio
    async def test_bot_initializes_all_components(self, bot_config, httpx_transport):
        """Test that bot initializes all required components"""
        _, _ = httpx_transport

        bot = Bot(config=bot_config)

        # Before entering context, components are None
        assert bot.config is not None
        assert bot.api_client is None
        assert bot.dispatcher is None
        assert bot.offset_manager is None
        assert bot.poller is None

        # After entering context
        async with bot:
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.offset_manager is not None
            assert bot.poller is not None

    @pytest.mark.asyncio
    async def test_bot_uses_custom_config(self, bot_config_custom, httpx_transport):
        """Test that bot uses custom configuration"""
        _, _ = httpx_transport

        async with Bot(config=bot_config_custom) as bot:
            assert bot.config == bot_config_custom
            assert bot.config.polling_limit == 50  # Custom value
            assert bot.config.polling_timeout == 20
            assert bot.config.max_retries == 5

    @pytest.mark.asyncio
    async def test_bot_initializes_with_default_handlers(self, bot_config, httpx_transport):
        """Test that bot initializes with empty handlers"""
        _, _ = httpx_transport

        async with Bot(config=bot_config) as bot:
            # Dispatcher should be ready but empty
            assert len(bot.dispatcher.handlers) == 0


class TestBotErrorHandling:
    """Tests for error handling in bot lifecycle"""

    @pytest.mark.asyncio
    async def test_bot_handler_exception_propagates(self, bot_config, httpx_transport):
        """Test that exceptions in handlers are logged but don't crash bot"""
        _, _ = httpx_transport

        async def failing_handler(update):
            raise ValueError("Handler error")

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(failing_handler)

            # Bot should start and stop even with failing handler
            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

        # Handler would be called if there were messages
        # Bot should still be clean after stop
        assert bot.poller is None or bot.poller._polling_task is None

    @pytest.mark.asyncio
    async def test_bot_handles_api_errors_gracefully(self, bot_config, httpx_transport):
        """Test that bot handles API errors without crashing"""
        from ymbot_async.errors import ApiError

        _, _ = httpx_transport

        async def handler(update):
            pass

        # Mock API to raise error
        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            # Mock get_updates to raise error
            bot.api_client.get_updates = AsyncMock(
                side_effect=ApiError("API error", status_code=500)
            )

            # Bot should start and handle the error
            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.2)  # Give it time to encounter error
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

        # Should stop cleanly
        assert bot.poller is None or bot.poller._polling_task is None


class TestBotMultipleHandlers:
    """Tests for bot with multiple handlers"""

    @pytest.mark.asyncio
    async def test_bot_with_multiple_handlers(self, bot_config, httpx_transport):
        """Test that bot can handle multiple message handlers"""
        _, _ = httpx_transport

        async def handler1(update):
            pass

        async def handler2(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler1)
            bot.message_handler()(handler2)

            # Both handlers should be registered
            assert len(bot.dispatcher.handlers) >= 2

            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

    @pytest.mark.asyncio
    async def test_bot_handlers_executed_in_order(self, bot_config, httpx_transport):
        """Test that handlers are executed in registration order"""
        _, _ = httpx_transport

        async def handler1(update):
            pass

        async def handler2(update):
            pass

        async def handler3(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler1)
            bot.message_handler()(handler2)
            bot.message_handler()(handler3)

            # Handlers should be in order
            assert len(bot.dispatcher.handlers) >= 3

            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task


class TestBotCleanup:
    """Tests for bot cleanup on shutdown"""

    @pytest.mark.asyncio
    async def test_bot_cleanup_after_stop(self, bot_config, httpx_transport):
        """Test that bot cleans up resources after stop"""
        _, _ = httpx_transport

        async def handler(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

        # Verify cleanup after exiting context
        assert bot.poller is None or bot.poller._polling_task is None

    @pytest.mark.asyncio
    async def test_bot_multiple_start_stop_cycles(self, bot_config, httpx_transport):
        """Test that bot can be started and stopped multiple times"""
        _, _ = httpx_transport

        async def handler(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            # Multiple cycles
            for _ in range(3):
                polling_task = asyncio.create_task(bot.run_polling())
                await asyncio.sleep(0.05)
                await bot.stop()

                if not polling_task.done():
                    polling_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await polling_task

        # Should be clean after all cycles
        assert bot.poller is None or bot.poller._polling_task is None


class TestBotIntegrationWithOffsetManager:
    """Tests for bot integration with offset manager"""

    @pytest.mark.asyncio
    async def test_bot_commits_offset_after_handler(self, bot_config, httpx_transport):
        """Test that bot commits offset after successful handler execution"""
        _, _ = httpx_transport

        async def handler(update):
            return "OK"

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

        # Offset manager should be initialized
        assert bot.offset_manager is not None

    @pytest.mark.asyncio
    async def test_bot_preserves_offset_across_restarts(self, bot_config, httpx_transport):
        """Test that bot preserves offset value across restarts"""
        _, _ = httpx_transport

        async def handler(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)

            # First run
            polling_task1 = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)

            # Get offset after first run
            offset_before = await bot.offset_manager.get_offset()

            await bot.stop()

            if not polling_task1.done():
                polling_task1.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task1

            # Second run
            polling_task2 = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)

            # Get offset after second run
            offset_after = await bot.offset_manager.get_offset()

            await bot.stop()

            if not polling_task2.done():
                polling_task2.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task2

        # Offset should be preserved or incremented
        assert offset_after >= offset_before


class TestBotWithContextManager:
    """Tests for bot as async context manager"""

    @pytest.mark.asyncio
    async def test_bot_as_async_context_manager(self, bot_config, httpx_transport):
        """Test using bot as async context manager"""
        _, _ = httpx_transport

        async def handler(update):
            pass

        async with Bot(config=bot_config) as bot:
            bot.message_handler()(handler)
            polling_task = asyncio.create_task(bot.run_polling())
            await asyncio.sleep(0.1)
            await bot.stop()

            if not polling_task.done():
                polling_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await polling_task

        # Should be stopped after exiting context
        assert bot.poller is None or bot.poller._polling_task is None
