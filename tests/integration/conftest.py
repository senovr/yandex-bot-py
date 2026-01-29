"""Fixtures for integration tests"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ymbot_async.api.client import ApiClient
from ymbot_async.config import BotConfig
from ymbot_async.transport.httpx_transport import HttpxTransport


@pytest.fixture
def bot_config() -> BotConfig:
    """Create a test bot configuration."""
    return BotConfig(token="test_token_123")


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient."""
    from httpx import Response

    client = MagicMock()

    # Create a mock response
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={"result": []})
    mock_response.content = b'{"result": []}'
    mock_response.headers = {}

    # Mock async methods
    client.request = AsyncMock(return_value=mock_response)
    client.get = AsyncMock(return_value=mock_response)
    client.post = AsyncMock(return_value=mock_response)
    client.aclose = AsyncMock()

    # Mock async context manager
    async def mock_aenter():
        return client

    async def mock_aexit(*args):
        await client.aclose()

    client.__aenter__ = mock_aenter
    client.__aexit__ = mock_aexit

    return client


@pytest.fixture
def httpx_transport(bot_config, mock_httpx_client):
    """Create an HTTP transport with mocked httpx client."""
    with patch(
        "ymbot_async.transport.httpx_transport.httpx.AsyncClient", return_value=mock_httpx_client
    ):
        transport = HttpxTransport(bot_config)
        yield transport, mock_httpx_client


@pytest.fixture
def mocked_transport():
    """Create a mocked HttpxTransport for API client testing."""
    transport = AsyncMock()
    transport.request = AsyncMock()
    return transport


@pytest.fixture
def api_client_with_mock(mocked_transport):
    """Create ApiClient with mocked transport."""
    return ApiClient(mocked_transport)


@pytest.fixture
def bot_config_custom():
    """Create a custom bot configuration for testing."""
    from ymbot_async.config import BotConfig

    return BotConfig(
        token="custom_token_456",
        base_url="https://custom.api.example.com",
        timeout_connect=10,
        timeout_read=30,
        timeout_write=10,
        max_connections=50,
        max_retries=5,
        retry_backoff_base=1.0,
        retry_backoff_max=30.0,
        polling_limit=50,
        polling_timeout=20,
        polling_backoff=1.0,
        polling_max_backoff=60.0,
    )


@pytest.fixture
def bot_config_custom_backoff_max():
    """Create a bot configuration with custom max_backoff."""
    from ymbot_async.config import BotConfig

    return BotConfig(
        token="backoff_token_789",
        max_retries=3,
        retry_backoff_base=0.5,
        retry_backoff_max=5.0,
        polling_max_backoff=10.0,
    )
