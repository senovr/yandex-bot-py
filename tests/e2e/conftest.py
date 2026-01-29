"""Configuration for E2E tests"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from ymbot_async.api.schemas import Update

# Load .env file if it exists
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


@pytest.fixture
def real_bot_config():
    """
    Fixture for real bot configuration.

    This fixture checks for REAL_BOT_TOKEN environment variable.
    Tests requiring real API will be skipped if token is not provided.
    """
    token = os.getenv("REAL_BOT_TOKEN")

    if not token:
        pytest.skip("REAL_BOT_TOKEN environment variable not set")

    from ymbot_async.config import BotConfig

    return BotConfig(
        token=token,
        base_url="https://botapi.messenger.yandex.net/bot/v1",
        log_level="DEBUG",
        log_format="text",
    )


@pytest.fixture
def sample_update():
    """Fixture providing a sample update object for E2E tests."""
    return Update.model_validate(
        {
            "update_id": 1,
            "message_id": 123,
            "timestamp": 1702323240,
            "chat": {"type": "private"},
            "from": {"login": "test_user", "display_name": "Test User"},
            "text": "Hello",
        }
    )
