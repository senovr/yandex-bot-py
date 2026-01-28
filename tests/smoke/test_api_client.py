"""Smoke tests for ApiClient"""

import pytest
from unittest.mock import AsyncMock


class TestApiClientInitialization:
    """Tests for API client initialization"""

    def test_api_client_initialization(self, api_client):
        """Test that API client can be initialized."""
        assert api_client is not None
        assert api_client.transport is not None


class TestApiClientMethods:
    """Tests that API client methods exist and are callable"""

    @pytest.mark.asyncio
    async def test_get_updates_method_exists(self, api_client, mock_transport):
        """Test that get_updates method exists and can be called."""
        # Mock response with proper schema
        mock_transport.request.return_value = {
            "ok": True,
            "updates": []
        }

        result = await api_client.get_updates()
        
        assert result is not None
        assert result.ok is True
        assert mock_transport.request.called

    @pytest.mark.asyncio
    async def test_send_message_method_exists(self, api_client, mock_transport):
        """Test that send_message method exists and can be called."""
        # Mock response with proper schema
        mock_transport.request.return_value = {
            "ok": True,
            "message": {
                "id": "123",
                "text": "Hello, World!",
                "timestamp": "2026-01-27T19:00:00Z",
                "chat": {
                    "id": "456",
                    "type": "private",
                    "name": "Test Chat"
                }
            }
        }
        
        result = await api_client.send_message(
            chat_id="456",
            text="Hello, World!"
        )
        
        assert result is not None
        assert result.ok is True
        assert mock_transport.request.called

    @pytest.mark.asyncio
    async def test_answer_callback_query_method_exists(self, api_client, mock_transport):
        """Test that answer_callback_query method exists and can be called."""
        mock_transport.request.return_value = {}
        
        result = await api_client.answer_callback_query(
            callback_query_id="123",
            text="Clicked!"
        )
        
        assert result is not None
        assert mock_transport.request.called

    @pytest.mark.asyncio
    async def test_edit_message_text_method_exists(self, api_client, mock_transport):
        """Test that edit_message_text method exists and can be called."""
        # Mock response with proper schema
        mock_transport.request.return_value = {
            "ok": True,
            "message": {
                "id": "123",
                "text": "Edited text",
                "timestamp": "2026-01-27T19:00:00Z",
                "chat": {
                    "id": "456",
                    "type": "private",
                    "name": "Test Chat"
                }
            }
        }
        
        result = await api_client.edit_message_text(
            chat_id="456",
            message_id="789",
            text="Edited text"
        )
        
        assert result is not None
        assert result.ok is True
        assert mock_transport.request.called

    @pytest.mark.asyncio
    async def test_delete_message_method_exists(self, api_client, mock_transport):
        """Test that delete_message method exists and can be called."""
        mock_transport.request.return_value = {}
        
        result = await api_client.delete_message(
            chat_id="456",
            message_id="789"
        )
        
        assert result is not None
        assert mock_transport.request.called