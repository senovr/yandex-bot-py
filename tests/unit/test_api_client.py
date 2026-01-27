"""Unit tests for ApiClient"""
from unittest.mock import AsyncMock

import pytest

from ymbot_async.api.client import ApiClient
from ymbot_async.api.schemas import (
    GetUpdatesResponse,
    MessageResponse,
    SendMessageRequest,
    InlineButton,
    InlineKeyboardMarkup,
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
        api_client.transport.request = AsyncMock(
            return_value={"ok": True, "updates": []}
        )

        result = await api_client.get_updates()

        assert isinstance(result, GetUpdatesResponse)
        assert result.ok is True
        api_client.transport.request.assert_called_once()
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["path"] == "/messages/getUpdates"
        assert call_kwargs["params"]["limit"] == 100
        assert call_kwargs["params"]["timeout"] == 1.0
        assert "offset" not in call_kwargs["params"]

    @pytest.mark.asyncio
    async def test_get_updates_with_offset(self, api_client):
        """Test get_updates with offset parameter"""
        api_client.transport.request = AsyncMock(
            return_value={"ok": True, "updates": []}
        )

        await api_client.get_updates(offset=10)

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["params"]["offset"] == 10

    @pytest.mark.asyncio
    async def test_get_updates_with_limit(self, api_client):
        """Test get_updates with custom limit"""
        api_client.transport.request = AsyncMock(
            return_value={"ok": True, "updates": []}
        )

        await api_client.get_updates(limit=50)

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["params"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_updates_with_timeout(self, api_client):
        """Test get_updates with custom timeout"""
        api_client.transport.request = AsyncMock(
            return_value={"ok": True, "updates": []}
        )

        await api_client.get_updates(timeout=5.0)

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["params"]["timeout"] == 5.0

    @pytest.mark.asyncio
    async def test_get_updates_with_all_params(self, api_client):
        """Test get_updates with all parameters"""
        api_client.transport.request = AsyncMock(
            return_value={"ok": True, "updates": []}
        )

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
                    "message": {
                        "id": "1",
                        "text": "Hello",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "chat": {"id": "chat_123", "type": "private"},
                    }
                }
            ]
        }
        api_client.transport.request = AsyncMock(return_value=response_data)

        result = await api_client.get_updates()

        assert result.ok is True
        assert len(result.updates) == 1
        assert result.updates[0].update_id == 1
        assert result.updates[0].message.text == "Hello"


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
                "message": {
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
        )

        result = await api_client.send_message(chat_id="chat_123", text="Hello")

        assert isinstance(result, MessageResponse)
        assert result.ok is True
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/sendMessage"
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_message_with_parse_mode(self, api_client):
        """Test send_message with parse_mode"""
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
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
        )

        await api_client.send_message(
            chat_id="chat_123",
            text="Hello",
            parse_mode="Markdown"
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_send_message_with_keyboard(self, api_client):
        """Test send_message with inline keyboard"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineButton(text="Click", url=None, callback_data="btn")]]
        )
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
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
        )

        await api_client.send_message(
            chat_id="chat_123",
            text="Hello",
            reply_markup=keyboard
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert "reply_markup" in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_send_message_with_all_params(self, api_client):
        """Test send_message with all parameters"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineButton(text="Click", url="https://example.com", callback_data=None)]]
        )
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
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
        )

        await api_client.send_message(
            chat_id="chat_123",
            text="Hello",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["text"] == "Hello"
        assert call_kwargs["json"]["parse_mode"] == "HTML"
        assert "reply_markup" in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_send_message_parse_response(self, api_client, sample_message):
        """Test send_message parses response correctly"""
        response_data = {
            "ok": True,
            "message": sample_message.model_dump()
        }
        api_client.transport.request = AsyncMock(return_value=response_data)

        result = await api_client.send_message(chat_id="chat_123", text="Hello")

        assert result.ok is True
        assert result.message.id == sample_message.id


class TestApiClientAnswerCallbackQuery:
    """Tests for answer_callback_query method"""

    @pytest.fixture
    def api_client(self, mock_transport):
        """Create ApiClient instance"""
        return ApiClient(mock_transport)

    @pytest.mark.asyncio
    async def test_answer_callback_query_basic(self, api_client):
        """Test answer_callback_query with basic parameters"""
        api_client.transport.request = AsyncMock(return_value={"ok": True})

        await api_client.answer_callback_query(callback_query_id="query_123")

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/answerCallbackQuery"
        assert call_kwargs["json"]["callback_query_id"] == "query_123"
        assert call_kwargs["json"]["show_alert"] is False

    @pytest.mark.asyncio
    async def test_answer_callback_query_with_text(self, api_client):
        """Test answer_callback_query with text"""
        api_client.transport.request = AsyncMock(return_value={"ok": True})

        await api_client.answer_callback_query(
            callback_query_id="query_123",
            text="Clicked!"
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["text"] == "Clicked!"

    @pytest.mark.asyncio
    async def test_answer_callback_query_with_alert(self, api_client):
        """Test answer_callback_query with show_alert"""
        api_client.transport.request = AsyncMock(return_value={"ok": True})

        await api_client.answer_callback_query(
            callback_query_id="query_123",
            text="Error!",
            show_alert=True
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["show_alert"] is True

    @pytest.mark.asyncio
    async def test_answer_callback_query_with_all_params(self, api_client):
        """Test answer_callback_query with all parameters"""
        api_client.transport.request = AsyncMock(return_value={"ok": True})

        await api_client.answer_callback_query(
            callback_query_id="query_123",
            text="Success",
            show_alert=False
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["callback_query_id"] == "query_123"
        assert call_kwargs["json"]["text"] == "Success"
        assert call_kwargs["json"]["show_alert"] is False


class TestApiClientEditMessageText:
    """Tests for edit_message_text method"""

    @pytest.fixture
    def api_client(self, mock_transport):
        """Create ApiClient instance"""
        return ApiClient(mock_transport)

    @pytest.mark.asyncio
    async def test_edit_message_text_basic(self, api_client):
        """Test edit_message_text with basic parameters"""
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
                    "id": "123",
                    "text": "New text",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "chat": {
                        "id": "chat_123",
                        "type": "private",
                        "name": "Test Chat",
                    },
                },
            }
        )

        result = await api_client.edit_message_text(
            chat_id="chat_123",
            message_id="msg_456",
            text="New text"
        )

        assert isinstance(result, MessageResponse)
        assert result.ok is True
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/editMessageText"
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["message_id"] == "msg_456"
        assert call_kwargs["json"]["text"] == "New text"

    @pytest.mark.asyncio
    async def test_edit_message_text_with_parse_mode(self, api_client):
        """Test edit_message_text with parse_mode"""
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
                    "id": "123",
                    "text": "New text",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "chat": {
                        "id": "chat_123",
                        "type": "private",
                        "name": "Test Chat",
                    },
                },
            }
        )

        await api_client.edit_message_text(
            chat_id="chat_123",
            message_id="msg_456",
            text="New text",
            parse_mode="Markdown"
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_edit_message_text_with_keyboard(self, api_client):
        """Test edit_message_text with inline keyboard"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineButton(text="Click", url=None, callback_data="btn")]]
        )
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
                    "id": "123",
                    "text": "New text",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "chat": {
                        "id": "chat_123",
                        "type": "private",
                        "name": "Test Chat",
                    },
                },
            }
        )

        await api_client.edit_message_text(
            chat_id="chat_123",
            message_id="msg_456",
            text="New text",
            reply_markup=keyboard
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert "reply_markup" in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_edit_message_text_with_all_params(self, api_client):
        """Test edit_message_text with all parameters"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineButton(text="Button", url="https://example.com", callback_data=None)]]
        )
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
                    "id": "123",
                    "text": "New text",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "chat": {
                        "id": "chat_123",
                        "type": "private",
                        "name": "Test Chat",
                    },
                },
            }
        )

        await api_client.edit_message_text(
            chat_id="chat_123",
            message_id="msg_456",
            text="New text",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["message_id"] == "msg_456"
        assert call_kwargs["json"]["text"] == "New text"
        assert call_kwargs["json"]["parse_mode"] == "HTML"
        assert "reply_markup" in call_kwargs["json"]


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

        result = await api_client.delete_message(
            chat_id="chat_123",
            message_id="msg_456"
        )

        assert result == {"ok": True}
        call_kwargs = api_client.transport.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/deleteMessage"
        assert call_kwargs["json"]["chat_id"] == "chat_123"
        assert call_kwargs["json"]["message_id"] == "msg_456"


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
        api_client.transport.request = AsyncMock(
            side_effect=TransportError("Connection failed")
        )

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


class TestApiClientRequestFormatting:
    """Tests for request formatting"""

    @pytest.fixture
    def api_client(self, mock_transport):
        """Create ApiClient instance"""
        return ApiClient(mock_transport)

    @pytest.mark.asyncio
    async def test_send_message_excludes_none_values(self, api_client):
        """Test that send_message excludes None values from request"""
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
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
        )

        await api_client.send_message(
            chat_id="chat_123",
            text="Hello",
            parse_mode=None,
            reply_markup=None
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert "parse_mode" not in call_kwargs["json"]
        assert "reply_markup" not in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_edit_message_text_excludes_none_values(self, api_client):
        """Test that edit_message_text excludes None values"""
        api_client.transport.request = AsyncMock(
            return_value={
                "ok": True,
                "message": {
                    "id": "123",
                    "text": "New text",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "chat": {
                        "id": "chat_123",
                        "type": "private",
                        "name": "Test Chat",
                    },
                },
            }
        )

        await api_client.edit_message_text(
            chat_id="chat_123",
            message_id="msg_456",
            text="New text",
            parse_mode=None,
            reply_markup=None
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert "parse_mode" not in call_kwargs["json"]
        assert "reply_markup" not in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_answer_callback_query_excludes_none_text(self, api_client):
        """Test that answer_callback_query excludes text when None"""
        api_client.transport.request = AsyncMock(return_value={"ok": True})

        await api_client.answer_callback_query(
            callback_query_id="query_123",
            text=None,
            show_alert=False
        )

        call_kwargs = api_client.transport.request.call_args[1]
        assert "text" not in call_kwargs["json"]