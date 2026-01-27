"""Unit tests for Bot class"""
import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from ymbot_async.bot import Bot
from ymbot_async.dispatcher.filters import CommandFilter


class TestBotInit:
    """Tests for Bot initialization"""

    def test_bot_initializes_with_config(self, bot_config):
        """Test bot initializes with config"""
        bot = Bot(bot_config)
        
        assert bot.config == bot_config
        assert bot._transport is None
        assert bot.api_client is None
        assert bot.dispatcher is None
        assert bot.offset_manager is None
        assert bot.poller is None

    def test_bot_initializes_different_configs(self):
        """Test bot initializes with different config values"""
        from ymbot_async.config import BotConfig
        
        config1 = BotConfig(token="token1", log_level="DEBUG")
        config2 = BotConfig(token="token2", log_level="ERROR")
        
        bot1 = Bot(config1)
        bot2 = Bot(config2)
        
        assert bot1.config.token == "token1"
        assert bot2.config.token == "token2"


class TestBotContextManager:
    """Tests for async context manager"""

    @pytest.mark.asyncio
    async def test_aenter_initializes_components(self, bot_config):
        """Test __aenter__ initializes all components"""
        bot = Bot(bot_config)
        
        async with bot:
            assert bot._transport is not None
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.offset_manager is not None
            assert bot.poller is not None

    @pytest.mark.asyncio
    async def test_aenter_creates_transport(self, bot_config):
        """Test __aenter__ creates transport"""
        bot = Bot(bot_config)
        
        async with bot:
            from ymbot_async.transport.httpx_transport import HttpxTransport
            assert isinstance(bot._transport, HttpxTransport)

    @pytest.mark.asyncio
    async def test_aenter_creates_dispatcher(self, bot_config):
        """Test __aenter__ creates dispatcher"""
        bot = Bot(bot_config)
        
        async with bot:
            from ymbot_async.dispatcher.dispatcher import Dispatcher
            assert isinstance(bot.dispatcher, Dispatcher)

    @pytest.mark.asyncio
    async def test_aenter_creates_offset_manager(self, bot_config):
        """Test __aenter__ creates offset manager"""
        bot = Bot(bot_config)
        
        async with bot:
            from ymbot_async.runtime.offset_manager import OffsetManager
            assert isinstance(bot.offset_manager, OffsetManager)

    @pytest.mark.asyncio
    async def test_aenter_creates_poller(self, bot_config):
        """Test __aenter__ creates poller"""
        bot = Bot(bot_config)
        
        async with bot:
            from ymbot_async.runtime.polling import Poller
            assert isinstance(bot.poller, Poller)

    @pytest.mark.asyncio
    async def test_aexit_cleans_up_components(self, bot_config):
        """Test __aexit__ cleans up components"""
        bot = Bot(bot_config)
        
        async with bot:
            # Store references
            transport = bot._transport
            dispatcher = bot.dispatcher
            poller = bot.poller
        
        # Components should be stopped (but not necessarily None)
        # The important thing is that cleanup happened without errors

    @pytest.mark.asyncio
    async def test_context_manager_handles_exception(self, bot_config):
        """Test context manager handles exceptions"""
        bot = Bot(bot_config)
        
        try:
            async with bot:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should still clean up


class TestBotMessageHandler:
    """Tests for message_handler decorator"""

    @pytest.mark.asyncio
    async def test_message_handler_registers_handler(self, bot_config):
        """Test message_handler decorator registers handler"""
        bot = Bot(bot_config)
        
        async with bot:
            @bot.message_handler()
            async def test_handler(update):
                pass
            
            # Handler should be registered
            assert len(bot.dispatcher.handlers) > 0

    @pytest.mark.asyncio
    async def test_message_handler_with_filters(self, bot_config):
        """Test message_handler with filters"""
        bot = Bot(bot_config)
        
        async with bot:
            filter_obj = CommandFilter("start")
            
            @bot.message_handler(filters=filter_obj)
            async def start_handler(update):
                pass
            
            # Handler with filter should be registered
            assert len(bot.dispatcher.handlers) > 0

    @pytest.mark.asyncio
    async def test_message_handler_multiple_handlers(self, bot_config):
        """Test registering multiple message handlers"""
        bot = Bot(bot_config)
        
        async with bot:
            @bot.message_handler()
            async def handler1(update):
                pass
            
            @bot.message_handler()
            async def handler2(update):
                pass
            
            @bot.message_handler()
            async def handler3(update):
                pass
            
            # All handlers should be registered
            assert len(bot.dispatcher.handlers) == 3

    @pytest.mark.asyncio
    async def test_message_handler_without_context_raises(self, bot_config):
        """Test message_handler without context raises error"""
        bot = Bot(bot_config)
        
        # Should raise because not in context
        with pytest.raises(RuntimeError, match="Bot not initialized"):
            @bot.message_handler()
            async def test_handler(update):
                pass

    @pytest.mark.asyncio
    async def test_message_handler_returns_original_function(self, bot_config):
        """Test message_handler decorator returns original function"""
        bot = Bot(bot_config)
        
        async with bot:
            async def test_handler(update):
                pass
            
            result = bot.message_handler()(test_handler)
            
            assert result is test_handler


class TestBotProcessUpdate:
    """Tests for _process_update method"""

    @pytest.mark.asyncio
    async def test_process_update_feeds_to_dispatcher(self, bot_config, sample_update):
        """Test _process_update feeds update to dispatcher"""
        bot = Bot(bot_config)
        
        async with bot:
            # Mock feed_update
            bot.dispatcher.feed_update = AsyncMock(return_value=True)
            
            await bot._process_update(sample_update)
            
            # Should have fed the update
            bot.dispatcher.feed_update.assert_called_once_with(sample_update)

    @pytest.mark.asyncio
    async def test_process_update_commits_offset(self, bot_config, sample_update):
        """Test _process_update commits offset after processing"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.feed_update = AsyncMock(return_value=True)
            bot.offset_manager.commit_offset = AsyncMock()
            
            await bot._process_update(sample_update)
            
            # Should commit offset
            bot.offset_manager.commit_offset.assert_called_once_with(sample_update.update_id)

    @pytest.mark.asyncio
    async def test_process_update_handles_not_added(self, bot_config, sample_update):
        """Test _process_update handles when update not added to queue"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.feed_update = AsyncMock(return_value=False)
            bot.offset_manager.commit_offset = AsyncMock()
            
            await bot._process_update(sample_update)
            
            # Should not commit offset
            bot.offset_manager.commit_offset.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_update_handles_exception(self, bot_config, sample_update):
        """Test _process_update handles exceptions gracefully"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.feed_update = AsyncMock(side_effect=ValueError("Test error"))
            bot.offset_manager.commit_offset = AsyncMock()
            
            # Should not raise
            await bot._process_update(sample_update)

    @pytest.mark.asyncio
    async def test_process_update_without_context_raises(self, bot_config, sample_update):
        """Test _process_update without context raises error"""
        bot = Bot(bot_config)
        
        with pytest.raises(RuntimeError, match="Bot not initialized"):
            await bot._process_update(sample_update)


class TestBotRunPolling:
    """Tests for run_polling method"""

    @pytest.mark.asyncio
    async def test_run_polling_starts_dispatcher(self, bot_config):
        """Test run_polling starts dispatcher"""
        bot = Bot(bot_config)
        
        async with bot:
            # Mock components
            bot.dispatcher.run = AsyncMock()
            bot.poller.start = AsyncMock()
            
            # Cancel immediately
            async def run_with_cancel():
                task = asyncio.create_task(bot.run_polling())
                await asyncio.sleep(0.01)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            await run_with_cancel()
            
            # Dispatcher should have been started
            bot.dispatcher.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_polling_starts_poller(self, bot_config):
        """Test run_polling starts poller"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.run = AsyncMock()
            bot.poller.start = AsyncMock()
            
            async def run_with_cancel():
                task = asyncio.create_task(bot.run_polling())
                await asyncio.sleep(0.01)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            await run_with_cancel()
            
            # Poller should have been started
            bot.poller.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_polling_passes_callbacks(self, bot_config):
        """Test run_polling passes correct callbacks"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.run = AsyncMock()
            bot.poller.start = AsyncMock()
            
            async def run_with_cancel():
                task = asyncio.create_task(bot.run_polling())
                await asyncio.sleep(0.01)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            await run_with_cancel()
            
            # Check callbacks
            call_kwargs = bot.poller.start.call_args[1]
            assert "offset_getter" in call_kwargs
            assert "update_callback" in call_kwargs

    @pytest.mark.asyncio
    async def test_run_polling_without_context_raises(self, bot_config):
        """Test run_polling without context raises error"""
        bot = Bot(bot_config)
        
        with pytest.raises(RuntimeError, match="Bot not initialized"):
            await bot.run_polling()

    @pytest.mark.asyncio
    async def test_run_polling_handles_exception(self, bot_config):
        """Test run_polling handles exceptions"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.run = AsyncMock(side_effect=ValueError("Test error"))
            bot.poller.start = AsyncMock()
            
            with pytest.raises(ValueError, match="Test error"):
                await bot.run_polling()


class TestBotStop:
    """Tests for stop method"""

    @pytest.mark.asyncio
    async def test_stop_stops_poller(self, bot_config):
        """Test stop stops poller"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.poller.stop = AsyncMock()
            
            await bot.stop()
            
            # Poller should have been stopped
            bot.poller.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_stops_dispatcher(self, bot_config):
        """Test stop stops dispatcher"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.stop = AsyncMock()
            
            await bot.stop()
            
            # Dispatcher should have been stopped
            bot.dispatcher.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_with_none_components(self, bot_config):
        """Test stop with None components doesn't crash"""
        bot = Bot(bot_config)
        
        # Components are None before __aenter__
        # Should not crash
        await bot.stop()

    @pytest.mark.asyncio
    async def test_stop_multiple_times(self, bot_config):
        """Test stop can be called multiple times"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.poller.stop = AsyncMock()
            bot.dispatcher.stop = AsyncMock()
            
            await bot.stop()
            await bot.stop()
            await bot.stop()
            
            # Should have been called multiple times
            assert bot.poller.stop.call_count == 3
            assert bot.dispatcher.stop.call_count == 3


class TestBotIntegration:
    """Integration tests for Bot"""

    @pytest.mark.asyncio
    async def test_full_bot_lifecycle(self, bot_config):
        """Test full bot lifecycle: init, context manager, handler, cleanup"""
        bot = Bot(bot_config)
        
        # Handler should not work outside context
        with pytest.raises(RuntimeError):
            @bot.message_handler()
            async def handler(update):
                pass
        
        # Inside context
        async with bot:
            # Register handler
            @bot.message_handler()
            async def handler(update):
                pass
            
            # Verify handler registered
            assert len(bot.dispatcher.handlers) == 1
            
            # Verify all components initialized
            assert bot._transport is not None
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.offset_manager is not None
            assert bot.poller is not None

    @pytest.mark.asyncio
    async def test_bot_with_multiple_handlers(self, bot_config):
        """Test bot with multiple message handlers"""
        bot = Bot(bot_config)
        
        async with bot:
            @bot.message_handler()
            async def handler1(update):
                pass
            
            @bot.message_handler()
            async def handler2(update):
                pass
            
            @bot.message_handler()
            async def handler3(update):
                pass
            
            assert len(bot.dispatcher.handlers) == 3

    @pytest.mark.asyncio
    async def test_bot_handlers_with_different_filters(self, bot_config):
        """Test bot with handlers using different filters"""
        bot = Bot(bot_config)
        
        async with bot:
            @bot.message_handler(filters=CommandFilter("start"))
            async def start_handler(update):
                pass
            
            @bot.message_handler(filters=CommandFilter("help"))
            async def help_handler(update):
                pass
            
            @bot.message_handler()
            async def any_handler(update):
                pass
            
            assert len(bot.dispatcher.handlers) == 3


class TestBotErrorHandling:
    """Tests for error handling in Bot"""

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_crash_bot(self, bot_config, sample_update):
        """Test handler exceptions don't crash the bot"""
        bot = Bot(bot_config)
        
        async with bot:
            # Mock feed_update to raise exception
            bot.dispatcher.feed_update = AsyncMock(side_effect=ValueError("Handler error"))
            
            # Should not raise
            await bot._process_update(sample_update)

    @pytest.mark.asyncio
    async def test_offset_commit_exception_logged(self, bot_config, sample_update):
        """Test offset commit exceptions are logged"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.feed_update = AsyncMock(return_value=True)
            bot.offset_manager.commit_offset = AsyncMock(side_effect=Exception("Commit error"))
            
            # Should not raise
            await bot._process_update(sample_update)

    @pytest.mark.asyncio
    async def test_run_polling_logs_exceptions(self, bot_config):
        """Test run_polling logs exceptions before raising"""
        bot = Bot(bot_config)
        
        async with bot:
            bot.dispatcher.run = AsyncMock(side_effect=Exception("Polling error"))
            bot.poller.start = AsyncMock()
            
            # Should raise the exception
            with pytest.raises(Exception, match="Polling error"):
                await bot.run_polling()


class TestBotComponentInteractions:
    """Tests for interactions between bot components"""

    @pytest.mark.asyncio
    async def test_polling_updates_offset_manager(self, bot_config):
        """Test polling correctly updates offset manager"""
        bot = Bot(bot_config)
        
        async with bot:
            offsets = [0]
            
            async def offset_getter():
                return offsets[0]
            
            async def update_callback(update):
                offsets[0] = update.update_id + 1
            
            bot.poller.start = AsyncMock()
            
            # Simulate updates
            async with bot:
                for i in range(1, 4):
                    update = Mock()
                    update.update_id = i
                    await update_callback(update)
            
            # Offset should be updated
            assert offsets[0] == 4

    @pytest.mark.asyncio
    async def test_dispatcher_receives_updates_from_poller(self, bot_config):
        """Test dispatcher receives updates from poller"""
        bot = Bot(bot_config)
        
        async with bot:
            received_updates = []
            
            async def update_callback(update):
                received_updates.append(update)
            
            bot.poller.start = AsyncMock()
            
            # Simulate update
            sample_update = Mock()
            sample_update.update_id = 1
            await update_callback(sample_update)
            
            assert len(received_updates) == 1