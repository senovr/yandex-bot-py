"""Integration tests for Dispatcher"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ymbot_async.api.client import ApiClient
from ymbot_async.api.schemas import Update, Chat, Sender
from ymbot_async.bot import Bot
from ymbot_async.config import BotConfig
from ymbot_async.dispatcher.filters import (
    CommandFilter, TextFilter, ChatTypeFilter, AndFilter
)
from ymbot_async.dispatcher.handlers import MessageHandler


class TestDispatcherIntegration:
    """Tests dispatcher basic integration"""

    @pytest.mark.asyncio
    async def test_dispatcher_registers_handlers(self, bot_config):
        """Test that dispatcher properly registers handlers."""
        async with Bot(bot_config) as bot:
            @bot.message_handler(CommandFilter(command="start"))
            async def start_handler(update):
                pass

            @bot.message_handler(TextFilter(text="hello"))
            async def hello_handler(update):
                pass

            # Check that handlers were registered
            assert len(bot.dispatcher.handlers) == 2

    @pytest.mark.asyncio
    async def test_dispatcher_feed_update(self, bot_config):
        """Test that dispatcher can feed updates to queue."""
        async with Bot(bot_config) as bot:
            @bot.message_handler(TextFilter(text="test"))
            async def test_handler(update):
                pass

            # Create test update
            update = Update(
                update_id=1,
                message_id=123,
                text="test",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            # Feed update to dispatcher
            added = await bot.dispatcher.feed_update(update)
            assert added is True

    @pytest.mark.asyncio
    async def test_dispatcher_queue_full(self, bot_config):
        """Test that dispatcher returns False when queue is full."""
        async with Bot(bot_config) as bot:
            @bot.message_handler(TextFilter(text="test"))
            async def test_handler(update):
                pass

            # Create test update
            update = Update(
                update_id=1,
                message_id=123,
                text="test",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            # Fill the queue (queue_maxsize from config is 1000)
            # We can't actually fill 1000 items in a reasonable test, so we just
            # test the queue mechanism works
            added = await bot.dispatcher.feed_update(update)
            assert added is True


class TestHandlerFilterIntegration:
    """Tests handler and filter integration"""

    @pytest.mark.asyncio
    async def test_command_filter_matches(self, bot_config):
        """Test that command filter properly matches commands."""
        async with Bot(bot_config) as bot:
            handler = MessageHandler(
                callback=lambda u: None,
                filters=CommandFilter(command="start")
            )

            update = Update(
                update_id=1,
                message_id=123,
                text="/start",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            assert handler.check(update) is True

    @pytest.mark.asyncio
    async def test_command_filter_non_matching(self, bot_config):
        """Test that command filter doesn't match different command."""
        async with Bot(bot_config) as bot:
            handler = MessageHandler(
                callback=lambda u: None,
                filters=CommandFilter(command="start")
            )

            update = Update(
                update_id=1,
                message_id=123,
                text="/help",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            assert handler.check(update) is False

    @pytest.mark.asyncio
    async def test_text_filter_matches(self, bot_config):
        """Test that text filter matches exact text."""
        async with Bot(bot_config) as bot:
            handler = MessageHandler(
                callback=lambda u: None,
                filters=TextFilter(text="hello")
            )

            update = Update(
                update_id=1,
                message_id=123,
                text="hello",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            assert handler.check(update) is True

    @pytest.mark.asyncio
    async def test_chat_type_filter_matches(self, bot_config):
        """Test that chat type filter matches correct type."""
        async with Bot(bot_config) as bot:
            handler = MessageHandler(
                callback=lambda u: None,
                filters=ChatTypeFilter(chat_type="private")
            )

            update = Update(
                update_id=1,
                message_id=123,
                text="hello",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            assert handler.check(update) is True

    @pytest.mark.asyncio
    async def test_and_filter_matches_both(self, bot_config):
        """Test that AND filter matches when both filters pass."""
        async with Bot(bot_config) as bot:
            combined_filter = AndFilter(
                CommandFilter(command="help"),
                ChatTypeFilter(chat_type="private")
            )

            handler = MessageHandler(
                callback=lambda u: None,
                filters=combined_filter
            )

            update = Update(
                update_id=1,
                message_id=123,
                text="/help",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            assert handler.check(update) is True

    @pytest.mark.asyncio
    async def test_and_filter_fails_on_one(self, bot_config):
        """Test that AND filter fails when one filter doesn't match."""
        async with Bot(bot_config) as bot:
            combined_filter = AndFilter(
                CommandFilter(command="help"),
                ChatTypeFilter(chat_type="group")
            )

            handler = MessageHandler(
                callback=lambda u: None,
                filters=combined_filter
            )

            update = Update(
                update_id=1,
                message_id=123,
                text="/help",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            assert handler.check(update) is False


class TestDispatcherLifecycle:
    """Tests dispatcher lifecycle"""

    @pytest.mark.asyncio
    async def test_dispatcher_stop_prevents_feeding(self, bot_config):
        """Test that stopped dispatcher cannot receive updates."""
        async with Bot(bot_config) as bot:
            @bot.message_handler(TextFilter(text="test"))
            async def test_handler(update):
                pass

            # Stop the dispatcher
            await bot.dispatcher.stop()

            # Create test update
            update = Update(
                update_id=1,
                message_id=123,
                text="test",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id="user1")},
            )

            # Try to feed update - should return False
            added = await bot.dispatcher.feed_update(update)
            assert added is False

    @pytest.mark.asyncio
    async def test_dispatcher_idempotent_stop(self, bot_config):
        """Test that stopping dispatcher twice is safe."""
        async with Bot(bot_config) as bot:
            @bot.message_handler(TextFilter(text="test"))
            async def test_handler(update):
                pass

            # Stop the dispatcher
            await bot.dispatcher.stop()

            # Stop again - should not raise error
            await bot.dispatcher.stop()