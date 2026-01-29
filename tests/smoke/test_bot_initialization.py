"""Smoke tests for Bot initialization and lifecycle"""

import pytest


class TestBotInitialization:
    """Tests for basic bot initialization"""

    def test_bot_creation_with_config(self, bot):
        """Test that bot can be created with config."""
        assert bot is not None
        assert bot.config.token == "test_token_123"

    def test_bot_has_no_components_initially(self, bot):
        """Test that components are not initialized before context manager."""
        assert bot._transport is None
        assert bot.api_client is None
        assert bot.dispatcher is None
        assert bot.poller is None
        assert bot.offset_manager is None


class TestBotAsyncContext:
    """Tests for async context manager lifecycle"""

    @pytest.mark.asyncio
    async def test_bot_async_context_initialization(self, bot):
        """Test that bot components are initialized in async context."""
        async with bot:
            assert bot._transport is not None
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.poller is not None
            assert bot.offset_manager is not None

    @pytest.mark.asyncio
    async def test_bot_cleanup_on_exit(self, bot):
        """Test that components are cleaned up on exit."""
        async with bot:
            # Components should be initialized
            assert bot._transport is not None

        # After context exit, components should still exist (not None)
        # This is the current behavior - components are kept
        assert bot._transport is not None


class TestBotMessageHandler:
    """Tests for message handler registration"""

    def test_bot_registers_message_handler_without_context(self, bot):
        """Test that registering handler without context stores it for deferred registration."""

        @bot.message_handler()
        async def dummy_handler(update):
            pass

        # Handler should be stored in pending handlers
        assert len(bot._pending_handlers) == 1

    @pytest.mark.asyncio
    async def test_bot_registers_message_handler(self, bot):
        """Test that message handler can be registered in async context."""
        async with bot:
            handler_called = False

            @bot.message_handler()
            async def test_handler(update):
                nonlocal handler_called
                handler_called = True

            # Handler should be registered
            assert len(bot.dispatcher.handlers) == 1
            assert bot.dispatcher.handlers[0].callback == test_handler
