"""Integration tests for ApiClient with fake HTTP responses"""

import pytest

from ymbot_async.api.schemas import (
    InlineButton,
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
                    "message_id": 1,
                    "text": "Hello",
                    "timestamp": 1704110400,
                    "chat": {"type": "private", "id": "chat1"},
                    "from": {"id": "user1", "display_name": "User 1"},
                },
                {
                    "update_id": 2,
                    "message_id": 2,
                    "text": "World",
                    "timestamp": 1704110460,
                    "chat": {"type": "private", "id": "chat1"},
                    "from": {"id": "user1", "display_name": "User 1"},
                },
            ],
        }
        mocked_transport.request.return_value = mock_response

        # Call get_updates
        response = await api_client_with_mock.get_updates(offset=0, limit=100, timeout=1.0)

        # Verify request was made correctly
        mocked_transport.request.assert_called_once_with(
            method="GET",
            path="/messages/getUpdates/",
            params={"offset": 0, "limit": 100, "timeout": 1.0},
        )

        # Verify response
        assert response.ok is True, "expected response.ok to be True"
        assert len(response.updates) == 2, f"expected 2 updates but got {len(response.updates)}"
        assert response.updates[0].update_id == 1, (
            f"expected first update.update_id to be 1 but got {response.updates[0].update_id}"
        )
        assert response.updates[0].text == "Hello", (
            f"expected first update.text to be 'Hello' but got '{response.updates[0].text}'"
        )
        assert response.updates[1].update_id == 2, (
            f"expected second update.update_id to be 2 but got {response.updates[1].update_id}"
        )
        assert response.updates[1].text == "World", (
            f"expected second update.text to be 'World' but got '{response.updates[1].text}'"
        )

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
            path="/messages/getUpdates/",
            params={"offset": 10, "limit": 100, "timeout": 1.0},
        )

    @pytest.mark.asyncio
    async def test_get_updates_custom_limit_timeout(self, api_client_with_mock, mocked_transport):
        """Test get_updates with custom limit and timeout"""
        mock_response = {"ok": True, "updates": []}
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.get_updates(limit=50, timeout=5.0)

        mocked_transport.request.assert_called_once_with(
            method="GET",
            path="/messages/getUpdates/",
            params={"limit": 50, "timeout": 5.0},
        )


class TestApiClientSendMessage:
    """Tests for send_message method"""

    @pytest.mark.asyncio
    async def test_send_message_success(self, api_client_with_mock, mocked_transport):
        """Test successful send_message"""
        mock_response = {
            "ok": True,
            "message_id": 1,
        }
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.send_message(chat_id="chat1", text="Test message")

        mocked_transport.request.assert_called_once()
        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/sendText/"
        assert call_kwargs["json"]["chat_id"] == "chat1"
        assert call_kwargs["json"]["text"] == "Test message"
        assert "parse_mode" not in call_kwargs["json"]

        assert response.ok is True
        assert response.message_id == 1

    @pytest.mark.asyncio
    async def test_send_message_with_login(self, api_client_with_mock, mocked_transport):
        """Test send_message with login parameter"""
        mock_response = {
            "ok": True,
            "message_id": 1,
        }
        mocked_transport.request.return_value = mock_response

        await api_client_with_mock.send_message(login="user1", text="Test message")

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["json"]["login"] == "user1"

    @pytest.mark.asyncio
    async def test_send_message_with_inline_keyboard(self, api_client_with_mock, mocked_transport):
        """Test send_message with inline keyboard"""
        mock_response = {
            "ok": True,
            "message_id": 1,
        }
        mocked_transport.request.return_value = mock_response

        keyboard = [
            [InlineButton(text="Button 1", callback_data="btn1")],
            [InlineButton(text="Button 2", url="https://example.com")],
        ]

        await api_client_with_mock.send_message(
            chat_id="chat1", text="Test message", inline_keyboard=keyboard
        )

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert "inline_keyboard" in call_kwargs["json"]


class TestApiClientDeleteMessage:
    """Tests for delete_message method"""

    @pytest.mark.asyncio
    async def test_delete_message_success(self, api_client_with_mock, mocked_transport):
        """Test successful delete_message"""
        mock_response = {"ok": True}
        mocked_transport.request.return_value = mock_response

        response = await api_client_with_mock.delete_message(chat_id="chat1", message_id="msg1")

        call_kwargs = mocked_transport.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["path"] == "/messages/delete/"
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
