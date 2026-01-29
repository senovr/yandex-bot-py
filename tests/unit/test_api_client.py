"""Unit tests for ApiClient"""

from unittest.mock import AsyncMock

import pytest

from ymbot_async.api.client import ApiClient
from ymbot_async.api.schemas import (
    GetUpdatesResponse,
    InlineButton,
    InlineKeyboardMarkup,
    MessageResponse,
)


class TestApiClient:
    """Tests for ApiClient"""

    @pytest.fixture
    def api_client(self, mock_transport):
        """Create ApiClient instance with mock transport"""
        return ApiClient(mock_transport)

    @pytest.mark.asyncio
    async def test_get_updates_default_params(self, api_client):
        """Test get_updates with default parameters"""
        api_client.transport.request = AsyncMock(return_value={"ok": True, "updates": []})

        result = await api_client.get_updates()

        assert isinstance(result, GetUpdatesResponse)
        assert result.ok is True
        api_client.transport.request.assert_called_once()
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["path"] == "/messages/getUpdates/"
        assert call_kwargs["params"]["limit"] == 100
        assert call_kwargs["params"]["timeout"] == 1.0
        assert "offset" not in call_kwargs["params"]

    @pytest.mark.asyncio
    async def test_get_updates_with_offset(self, api_client):
        """Test get_updates with offset parameter"""
        api_client.transport.request = AsyncMock(return_value={"ok": True, "updates": []})

        await api_client.get_updates(offset=10)

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["params"]["offset"] == 10

    @pytest.mark.asyncio
    async def test_get_updates_with_limit(self, api_client):
        """Test get_updates with custom limit"""
        api_client.transport.request = AsyncMock(return_value={"ok": True, "updates": []})

        await api_client.get_updates(limit=50)

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["params"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_updates_with_timeout(self, api_client):
        """Test get_updates with custom timeout"""
        api_client.transport.request = AsyncMock(return_value={"ok": True, "updates": []})

        await api_client.get_updates(timeout=5.0)

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["params"]["timeout"] == 5.0

    @pytest.mark.asyncio
    async def test_get_updates_with_all_params(self, api_client):
        """Test get_updates with all parameters"""
        api_client.transport.request = AsyncMock(return_value={"ok": True, "updates": []})

        await api_client.get_updates(offset=100, limit=200, timeout=10.0)

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["params"]["offset"] == 100
        assert call_kwargs["params"]["limit"] == 200
        assert call_kwargs["params"]["timeout"] == 10.0

    @pytest.mark.asyncio
    async def test_get_updates_with_response_data(self, api_client):
        """Test get_updates parses response data correctly"""
        response_data = {
            "ok": True,
            "updates": [
                {
                    "update_id": 1,
                    "message_id": 123,
                    "timestamp": 1704067200,
                    "chat": {"type": "private"},
                    "from": {"login": "test_user", "display_name": "Test User"},
                    "text": "Hello",
                }
            ],
        }
        api_client.transport.request = AsyncMock(return_value=response_data)

        result = await api_client.get_updates()

        assert result.ok is True
        assert len(result.updates) == 1
        assert result.updates[0].update_id == 1
        assert result.updates[0].text == "Hello"


class TestApiClientSendMessage:
    """Tests for send_message method"""

    @pytest.fixture
    def api_client(self, mock_transport):
        """Create ApiClient instance"""
        return ApiClient(mock_transport)

    @pytest.mark.asyncio
    async def test_send_message_basic(self, api_client):
        """Test send_message with basic parameters"""
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message_id": 123,
            }
        )

        result = await api_client.send_message(chat_id="chat_123", text="Hello")

        assert isinstance(result, MessageResponse)
        assert result.ok is True
        assert result.message_id == 123
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/sendText/"
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_message_with_keyboard(self, api_client):
        """Test send_message with inline keyboard"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineButton(text="Click", url=None, callback_data="btn")]]
        )
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message_id": 123,
            }
        )

        await api_client.send_message(
            chat_id="chat_123", text="Hello", inline_keyboard=keyboard.inline_keyboard
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert "inline_keyboard" in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_send_message_with_all_params(self, api_client):
        """Test send_message with all parameters"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineButton(text="Click", url="https://example.com", callback_data=None)]
            ]
        )
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message_id": 123,
            }
        )

        await api_client.send_message(
            chat_id="chat_123",
            text="Hello",
            inline_keyboard=keyboard.inline_keyboard,
            reply_message_id=456,
            disable_notification=True,
            important=True,
            disable_web_page_preview=True,
            thread_id=789,
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["text"] == "Hello"
        assert "inline_keyboard" in call_kwargs["json"]
        assert call_kwargs["json"]["reply_message_id"] == 456
        assert call_kwargs["json"]["disable_notification"] is True
        assert call_kwargs["json"]["important"] is True
        assert call_kwargs["json"]["disable_web_page_preview"] is True
        assert call_kwargs["json"]["thread_id"] == 789


class TestApiClientDeleteMessage:
    """Tests for delete_message method"""

    @pytest.fixture
    def api_client(self, mock_transport):
        """Create ApiClient instance"""
        return ApiClient(mock_transport)

    @pytest.mark.asyncio
    async def test_delete_message(self, api_client):
        """Test delete_message"""
        api_client.transport.request = AsyncMock(return_value={"ok": True})

        result = await api_client.delete_message(chat_id="chat_123", message_id=456)

        assert result == {"ok": True}
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/delete/"
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["message_id"] == 456

    @pytest.mark.asyncio
    async def test_delete_message_with_thread_id(self, api_client):
        """Test delete_message with thread_id"""
        api_client.transport.request = AsyncMock(return_value={"ok": True})

        result = await api_client.delete_message(chat_id="chat_123", message_id=456, thread_id=789)

        assert result == {"ok": True}
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["thread_id"] == 789


class TestApiClientErrorHandling:
    """Tests for error handling in ApiClient"""

    @pytest.fixture
    def api_client(self, mock_transport):
        """Create ApiClient instance"""
        return ApiClient(mock_transport)

    @pytest.mark.asyncio
    async def test_transport_error_propagates(self, api_client):
        """Test that transport errors propagate"""
        from ymbot_async.errors import TransportError

        api_client.transport.request = AsyncMock(side_effect=TransportError("Connection failed"))

        with pytest.raises(TransportError) as exc_info:
            await api_client.get_updates()
        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_error_propagates(self, api_client):
        """Test that API errors propagate"""
        from ymbot_async.errors import ApiError

        api_client.transport.request = AsyncMock(
            side_effect=ApiError("Invalid token", status_code=401)
        )

        with pytest.raises(ApiError) as exc_info:
            await api_client.send_message(chat_id="chat_123", text="Hello")
        assert "Invalid token" in str(exc_info.value)
        assert exc_info.value.status_code == 401
