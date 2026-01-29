"""Pytest configuration and shared fixtures"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import Request, Response

from ymbot_async.api.schemas import (
    Chat,
    InlineButton,
    InlineKeyboardMarkup,
    Sender,
    Update,
)
from ymbot_async.config import BotConfig, RetryConfig
from ymbot_async.transport.httpx_transport import HttpxTransport


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def bot_config():
    """Create a default BotConfig for testing."""
    return BotConfig(
        token="test_token_123",
        base_url="https://botapi.messenger.yandex.net/bot/v1",
        polling_limit=100,
        polling_timeout=1.0,
        queue_maxsize=100,
        concurrency=5,
    )


@pytest.fixture
def bot_config_custom():
    """Create a custom BotConfig for testing."""
    return BotConfig(
        token="custom_token_456",
        base_url="https://custom.api.com",
        timeout_connect=5.0,
        timeout_read=15.0,
        max_retries=5,
        polling_limit=50,
        concurrency=10,
        log_level="DEBUG",
        log_format="json",
    )


@pytest.fixture
def bot_config_no_jitter():
    """Create a BotConfig with jitter disabled for testing."""
    return BotConfig(
        token="test_token_123",
        base_url="https://botapi.messenger.yandex.net/bot/v1",
        retry_jitter=False,
    )


@pytest.fixture
def bot_config_custom_backoff_max():
    """Create a BotConfig with custom backoff max for testing."""
    return BotConfig(
        token="test_token_123",
        base_url="https://botapi.messenger.yandex.net/bot/v1",
        retry_backoff_max=5.0,
        retry_jitter=False,
    )


@pytest.fixture
def retry_config():
    """Create a default RetryConfig for testing."""
    return RetryConfig()


@pytest.fixture
def retry_config_custom():
    """Create a custom RetryConfig for testing."""
    return RetryConfig(
        max_retries=5,
        retryable_statuses={500, 502, 503, 504},
    )


@pytest.fixture
def sample_chat():
    """Create a sample Chat object."""
    return Chat(
        id="chat_123",
        type="group",
    )


@pytest.fixture
def sample_update(sample_chat):
    """Create a sample Update object."""
    return Update(
        update_id=1,
        message_id=1,
        timestamp=1704067200,  # 2024-01-01T00:00:00Z
        chat=sample_chat,
        **{
            "from": Sender(
                login="12345",
                display_name="Test User",
            )
        },
        text="Hello, World!",
    )


@pytest.fixture
def sample_inline_button():
    """Create a sample InlineButton."""
    return InlineButton(
        text="Click Me",
        callback_data="btn_click",
        url=None,
    )


@pytest.fixture
def sample_inline_keyboard(sample_inline_button):
    """Create a sample InlineKeyboardMarkup."""
    return InlineKeyboardMarkup(inline_keyboard=[[sample_inline_button]])


@pytest.fixture
def sample_inline_keyboard_buttons(sample_inline_button):
    """Create a sample inline keyboard as list of lists of buttons."""
    return [[sample_inline_button]]


@pytest.fixture
def api_response_ok():
    """Create a mock successful API response for send_message."""
    return {
        "ok": True,
        "result": {
            "id": "123",
            "text": "Hello",
            "timestamp": "2024-01-01T00:00:00Z",
            "chat": {
                "id": "chat_123",
                "type": "private",
                "name": "Test Chat",
            },
        },
    }


@pytest.fixture
def api_response_error():
    """Create a mock failed API response."""
    return {
        "ok": False,
        "description": "Bad Request",
        "error_code": 400,
    }


@pytest.fixture
def get_updates_response():
    """Create a mock getUpdates response."""
    return {
        "ok": True,
        "updates": [
            {
                "update_id": 1,
                "message_id": 1,
                "timestamp": 1704067200,
                "chat": {
                    "type": "private",
                },
                "from": {
                    "id": "12345",
                    "login": "test_user",
                    "display_name": "Test User",
                },
                "text": "/start",
            }
        ],
    }


@pytest.fixture
def mock_http_response(api_response_ok):
    """Create a mock httpx Response object."""
    request = Request("POST", "https://api.example.com/test")
    response = Response(
        200,
        request=request,
        json=api_response_ok,
    )
    return response


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_transport():
    """Create a mock HttpxTransport."""
    transport = MagicMock()
    transport.__aenter__ = AsyncMock(return_value=transport)
    transport.__aexit__ = AsyncMock(return_value=None)
    transport.request = AsyncMock()
    transport.get = AsyncMock()
    transport.post = AsyncMock()
    transport.close = AsyncMock()
    return transport


@pytest.fixture
def mock_api_client(mock_transport):
    """Create a mock ApiClient."""
    client = MagicMock()
    client.get_updates = AsyncMock()
    client.send_message = AsyncMock()
    client.delete_message = AsyncMock()
    return client


@pytest.fixture
def mock_dispatcher():
    """Create a mock Dispatcher."""
    dispatcher = MagicMock()
    dispatcher.register_handler = MagicMock()
    dispatcher.add_update = AsyncMock()
    dispatcher.start = AsyncMock()
    dispatcher.stop = AsyncMock()
    return dispatcher


@pytest.fixture
def mock_offset_manager():
    """Create a mock OffsetManager."""
    manager = MagicMock()
    manager.get_offset = MagicMock(return_value=0)
    manager.commit_offset = AsyncMock()
    manager.initialize = AsyncMock()
    return manager


@pytest.fixture
def mock_poller():
    """Create a mock Poller."""
    poller = MagicMock()
    poller.run = AsyncMock()
    poller.stop = AsyncMock()
    return poller


@pytest.fixture
def transport(bot_config):
    """Create a real HttpxTransport instance for testing."""
    return HttpxTransport(config=bot_config)


@pytest.fixture
def sample_command_update(sample_chat):
    """Create a sample command update."""
    return Update(
        update_id=1,
        message_id=1,
        timestamp=1704067200,
        chat=sample_chat,
        **{
            "from": Sender(
                login="12345",
                display_name="Test User",
            )
        },
        text="/start",
    )
