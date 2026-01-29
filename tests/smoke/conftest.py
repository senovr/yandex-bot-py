"""Fixtures for smoke tests"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ymbot_async.api.client import ApiClient
from ymbot_async.bot import Bot
from ymbot_async.config import BotConfig
from ymbot_async.transport.httpx_transport import HttpxTransport


@pytest.fixture
def bot_config() -> BotConfig:
    """Create a test bot configuration."""
    return BotConfig(token="test_token_123")


@pytest.fixture
def mock_transport():
    """Create a mock HTTP transport."""
    transport = MagicMock(spec=HttpxTransport)

    # Mock async context manager methods
    async def mock_aenter():
        return transport

    async def mock_aexit(*args):
        pass

    transport.__aenter__ = mock_aenter
    transport.__aexit__ = mock_aexit
    transport.request = AsyncMock()

    return transport


@pytest.fixture
def api_client(mock_transport) -> ApiClient:
    """Create an API client with mock transport."""
    return ApiClient(mock_transport)


@pytest.fixture
def bot(bot_config):
    """Create a bot instance for testing."""
    return Bot(bot_config)
