"""Integration tests for ApiClient with fake HTTP responses"""

import pytest

from ymbot_async.api.schemas import (
    Chat,
    InlineButton,
    InlineKeyboardMarkup,
    Message,
    Update,
    User,
)


class TestApiClientGetUpdates:
    """Tests for get_updates method"""

    @pytest.mark.asyncio
    async def test_get_updates_success(self, api_client_with_mock, mocked_transport):
        """Test successful get_updates with updates"""
        # Mock response
        mock_response = {
            "ok": True,
            "updates": [
                {
                    "update_id": 1,
                    "message": {
                        "id": "msg1",
                        "text": "Hello",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "from": {"id": "user1", "name": "User 1"},
                        "chat": {"id": "chat1", "type": "private"},
                    },
                },
                {
                    "update_id": 2,
                    "message": {
                        "id": "msg2",
                        "text": "World",
                        "timestamp": "2024-01-01T12:01:00Z",
                        "from": {"id": "user1", "name": "User 1"},
                        "chat": {"id": "chat1", "type": "private"},
                    },
                },
            ],
        }
        mocked_transport.request.return_value = mock_response

        # Call get_updates
        response = await api_client_with_mock.get_updates(
            offset=0, limit=100, timeout=1.0
        )

        # Verify request was made correctly
        mocked_transport.request.assert_called_once_with(
            method="GET",
            path="/messages/getUpdates",
            params={"offset": 0, "limit": 100, "timeout": 1.0},
        )

        # Verify response
        assert response.ok is True
        assert len(response.updates) == 2
        assert response.updates[0].update_id == 1
        assert response.updates[0].message.text == "Hello"
        assert response.updates[1].update_id == 2
        assert response.updates[1].message.text == "World"

    @pytest.mark.asyncio
    async def test_get_updates_empty(self, api_client_with_mock, mocked_transport):
        """Test get_updates with empty response"""
        mock_response = {"ok": True, "updates": []}
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.get_updates()

        assert response.ok is True
        assert response.updates == []

    @pytest.mark.asyncio
    async def test_get_updates_with_offset(self, api_client_with_mock, mocked_transport):
        """Test get_updates with offset parameter"""
        mock_response = {"ok": True, "updates": []}
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.get_updates(offset=10)

        mocked_transport.request.assert_called_once_with(
            method="GET",
            path="/messages/getUpdates",
            params={"offset": 10, "limit": 100, "timeout": 1.0},
        )

    @pytest.mark.asyncio
    async def test_get_updates_custom_limit_timeout(
        self, api_client_with_mock, mocked_transport
    ):
        """Test get_updates with custom limit and timeout"""
        mock_response = {"ok": True, "updates": []}
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.get_updates(limit=50, timeout=5.0)

        mocked_transport.request.assert_called_once_with(
            method="GET",
            path="/messages/getUpdates",
            params={"limit": 50, "timeout": 5.0},
        )


class TestApiClientSendMessage:
    """Tests for send_message method"""

    @pytest.mark.asyncio
    async def test_send_message_success(self, api_client_with_mock, mocked_transport):
        """Test successful send_message"""
        mock_response = {
            "ok": True,
            "message": {
                "id": "msg1",
                "text": "Test message",
                "timestamp": "2024-01-01T12:00:00Z",
                "from": {"id": "bot1", "name": "Bot"},
                "chat": {"id": "chat1", "type": "private"},
            },
        }
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.send_message(
            chat_id="chat1", text="Test message"
        )

        mocked_transport.request.assert_called_once()
        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/sendMessage"
        assert call_kwargs["json"]["chat_id"] == "chat1"
        assert call_kwargs["json"]["text"] == "Test message"
        assert "parse_mode" not in call_kwargs["json"]

        assert response.ok is True
        assert response.message.text == "Test message"

    @pytest.mark.asyncio
    async def test_send_message_with_parse_mode(self, api_client_with_mock, mocked_transport):
        """Test send_message with parse_mode"""
        mock_response = {
            "ok": True,
            "message": {
                "id": "msg1",
                "text": "Test message",
                "timestamp": "2024-01-01T12:00:00Z",
                "from": {"id": "bot1", "name": "Bot"},
                "chat": {"id": "chat1", "type": "private"},
            },
        }
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.send_message(
            chat_id="chat1", text="Test message", parse_mode="Markdown"
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["json"]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_send_message_with_keyboard(self, api_client_with_mock, mocked_transport):
        """Test send_message with inline keyboard"""
        mock_response = {
            "ok": True,
            "message": {
                "id": "msg1",
                "text": "Test message",
                "timestamp": "2024-01-01T12:00:00Z",
                "from": {"id": "bot1", "name": "Bot"},
                "chat": {"id": "chat1", "type": "private"},
            },
        }
        mocked_transport.request.return_value = mock_response

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineButton(text="Button 1", callback_data="btn1")],
                [InlineButton(text="Button 2", url="https://example.com")],
            ]
        )

        await api_client_with_mock.send_message(
            chat_id="chat1", text="Test message", reply_markup=keyboard
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert "reply_markup" in call_kwargs["json"]
        assert call_kwargs["json"]["reply_markup"]["inline_keyboard"] == [
            [{"text": "Button 1", "callback_data": "btn1"}],
            [{"text": "Button 2", "url": "https://example.com"}],
        ]


class TestApiClientAnswerCallbackQuery:
    """Tests for answer_callback_query method"""

    @pytest.mark.asyncio
    async def test_answer_callback_query_with_text(
        self, api_client_with_mock, mocked_transport
    ):
        """Test answer_callback_query with text"""
        mock_response = {"ok": True}
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.answer_callback_query(
            callback_query_id="cbq1", text="Callback handled"
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/answerCallbackQuery"
        assert call_kwargs["json"]["callback_query_id"] == "cbq1"
        assert call_kwargs["json"]["text"] == "Callback handled"
        assert call_kwargs["json"]["show_alert"] is False

        assert response["ok"] is True

    @pytest.mark.asyncio
    async def test_answer_callback_query_show_alert(
        self, api_client_with_mock, mocked_transport
    ):
        """Test answer_callback_query with show_alert"""
        mock_response = {"ok": True}
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.answer_callback_query(
            callback_query_id="cbq1", text="Error occurred", show_alert=True
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["json"]["show_alert"] is True

    @pytest.mark.asyncio
    async def test_answer_callback_query_no_text(
        self, api_client_with_mock, mocked_transport
    ):
        """Test answer_callback_query without text"""
        mock_response = {"ok": True}
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.answer_callback_query(callback_query_id="cbq1")

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert "text" not in call_kwargs["json"]


class TestApiClientEditMessageText:
    """Tests for edit_message_text method"""

    @pytest.mark.asyncio
    async def test_edit_message_text_success(self, api_client_with_mock, mocked_transport):
        """Test successful edit_message_text"""
        mock_response = {
            "ok": True,
            "message": {
                "id": "msg1",
                "text": "Updated message",
                "timestamp": "2024-01-01T12:01:00Z",
                "from": {"id": "bot1", "name": "Bot"},
                "chat": {"id": "chat1", "type": "private"},
            },
        }
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.edit_message_text(
            chat_id="chat1", message_id="msg1", text="Updated message"
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/editMessageText"
        assert call_kwargs["json"]["chat_id"] == "chat1"
        assert call_kwargs["json"]["message_id"] == "msg1"
        assert call_kwargs["json"]["text"] == "Updated message"

        assert response.ok is True
        assert response.message.text == "Updated message"

    @pytest.mark.asyncio
    async def test_edit_message_text_with_parse_mode(
        self, api_client_with_mock, mocked_transport
    ):
        """Test edit_message_text with parse_mode"""
        mock_response = {"ok": True, "message": {"id": "msg1", "text": "Updated", "timestamp": "2024-01-01T12:00:00Z", "from": {"id": "bot1", "name": "Bot"}, "chat": {"id": "chat1", "type": "private"}}}
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.edit_message_text(
            chat_id="chat1", message_id="msg1", text="Updated", parse_mode="HTML"
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["json"]["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_edit_message_text_with_keyboard(
        self, api_client_with_mock, mocked_transport
    ):
        """Test edit_message_text with keyboard"""
        mock_response = {"ok": True, "message": {"id": "msg1", "text": "Updated", "timestamp": "2024-01-01T12:00:00Z", "from": {"id": "bot1", "name": "Bot"}, "chat": {"id": "chat1", "type": "private"}}}
        mocked_transport.request.return_value = mock_response

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineButton(text="Button", callback_data="btn")]
            ]
        )

        await api_client_with_mock.edit_message_text(
            chat_id="chat1",
            message_id="msg1",
            text="Updated",
            reply_markup=keyboard,
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert "reply_markup" in call_kwargs["json"]


class TestApiClientDeleteMessage:
    """Tests for delete_message method"""

    @pytest.mark.asyncio
    async def test_delete_message_success(self, api_client_with_mock, mocked_transport):
        """Test successful delete_message"""
        mock_response = {"ok": True}
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.delete_message(
            chat_id="chat1", message_id="msg1"
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/deleteMessage"
        assert call_kwargs["json"]["chat_id"] == "chat1"
        assert call_kwargs["json"]["message_id"] == "msg1"

        assert response["ok"] is True


class TestApiClientErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_api_error_response_400(self, api_client_with_mock, mocked_transport):
        """Test handling of 400 Bad Request error"""
        mock_response = {"ok": False, "error_code": 400, "description": "Bad Request"}
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.get_updates()

        # API client doesn't raise on error responses, just returns them
        assert response.ok is False

    @pytest.mark.asyncio
    async def test_api_error_response_500(self, api_client_with_mock, mocked_transport):
        """Test handling of 500 Internal Server Error"""
        mock_response = {
            "ok": False,
            "error_code": 500,
            "description": "Internal Server Error",
        }
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.get_updates()

        assert response.ok is False

    @pytest.mark.asyncio
    async def test_network_error(self, api_client_with_mock, mocked_transport):
        """Test handling of network errors"""
        import httpx

        mocked_transport.request.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(httpx.ConnectError):
            await api_client_with_mock.get_updates()

    @pytest.mark.asyncio
    async def test_timeout_error(self, api_client_with_mock, mocked_transport):
        """Test handling of timeout errors"""
        import httpx

        mocked_transport.request.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(httpx.TimeoutException):
            await api_client_with_mock.get_updates()