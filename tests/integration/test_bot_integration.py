"""Integration tests for Bot"""

import pytest

from ymbot_async.bot import Bot


class TestBotLifecycleIntegration:
    """Tests for bot lifecycle integration"""

    @pytest.mark.asyncio
    async def test_bot_initializes_all_components(self, bot_config):
        """Test that bot initializes all components on start."""
        async with Bot(bot_config) as bot:
            # All components should be initialized
            assert bot._transport is not None
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.poller is not None
            assert bot.offset_manager is not None

    @pytest.mark.asyncio
    async def test_bot_context_manager_cleanup(self, bot_config):
        """Test that bot properly cleans up resources."""
        async with Bot(bot_config) as bot:
            # After context exit, resources should be cleaned up
            assert bot._transport is not None