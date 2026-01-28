"""Integration tests for HttpxTransport with mock responses"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from ymbot_async.config import BotConfig, RetryConfig
from ymbot_async.transport.httpx_transport import HttpxTransport
from ymbot_async.errors import TransportError, ApiError


def _create_response_mock(status_code: int, data: dict):
    """Helper to create a response mock with json method"""
    response_mock = MagicMock()
    response_mock.status_code = status_code
    
    def json_mock():
        return data
    
    response_mock.json = json_mock
    return response_mock


class TestTransportHttpTimeout:
    """Tests for HTTP timeout behavior"""

    @pytest.mark.asyncio
    async def test_retry_on_read_timeout(self):
        """Test that transport retries on read timeout"""
        config = BotConfig(token="test_token")
        
        # Mock httpx.AsyncClient
        mock_client = MagicMock()
        
        # First call raises timeout, second succeeds
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ReadTimeout("Read timeout")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config) as transport:
                response = await transport.request("GET", "/test")
                assert response["ok"] is True
                assert call_count[0] == 2  # Initial call + 1 retry

    @pytest.mark.asyncio
    async def test_retry_on_connect_timeout(self):
        """Test that transport retries on connect timeout"""
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ConnectTimeout("Connect timeout")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config) as transport:
                response = await transport.request("GET", "/test")
                assert response["ok"] is True
                assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_retry_on_write_timeout(self):
        """Test that transport retries on write timeout"""
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.WriteTimeout("Write timeout")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config) as transport:
                response = await transport.request("GET", "/test")
                assert response["ok"] is True
                assert call_count[0] == 2


class TestTransportNetworkErrors:
    """Tests for network error handling"""

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Test that transport retries on connection errors"""
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ConnectError("Connection refused")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config) as transport:
                response = await transport.request("GET", "/test")
                assert response["ok"] is True
                assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_retry_on_protocol_error(self):
        """Test that transport retries on protocol errors"""
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ProtocolError("SSL handshake failed")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config) as transport:
                response = await transport.request("GET", "/test")
                assert response["ok"] is True
                assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_retry_on_network_unreachable(self):
        """Test that transport retries on network unreachable"""
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ConnectError("Network unreachable")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config) as transport:
                response = await transport.request("GET", "/test")
                assert response["ok"] is True
                assert call_count[0] == 2


class TestTransportMultipleRetries:
    """Tests for multiple retry attempts"""

    @pytest.mark.asyncio
    async def test_multiple_retries_with_backoff(self):
        """Test that transport uses exponential backoff between retries"""
        # Use custom retry config with small backoff
        retry_config = RetryConfig(max_retries=2)
        config = BotConfig(token="test_token", retry_backoff_base=0.05, retry_backoff_max=0.5)
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise httpx.ReadTimeout("Timeout")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config, retry_config=retry_config) as transport:
                start_time = asyncio.get_event_loop().time()
                response = await transport.request("GET", "/test", retry_config=retry_config)
                elapsed = asyncio.get_event_loop().time() - start_time
                
                assert response["ok"] is True
                # Should have taken at least backoff time (0.05s)
                assert elapsed >= 0.04
                assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_exhaust_all_retries(self):
        """Test that transport raises error after exhausting retries"""
        # Custom retry config with small max_retries
        retry_config = RetryConfig(max_retries=1)
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        
        # Always timeout - use async function instead of AsyncMock with side_effect
        async def always_timeout(*args, **kwargs):
            raise httpx.ReadTimeout("Always timeout")
        
        mock_client.request = always_timeout
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config, retry_config=retry_config) as transport:
                # The error should be raised after exhausting retries
                with pytest.raises(TransportError, match=".*Request failed after.*"):
                    await transport.request("GET", "/test")


class TestTransportNonRetryable:
    """Tests for non-retryable errors"""

    @pytest.mark.asyncio
    async def test_4xx_status_not_retried(self):
        """Test that 4xx errors are not retried"""
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        # 400 error - should not retry - use async function instead of AsyncMock
        async def return_400(*args, **kwargs):
            call_count[0] += 1
            return _create_response_mock(400, {"ok": False, "error": "Bad Request"})
        
        mock_client.request = return_400
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(ApiError):
                async with HttpxTransport(config) as transport:
                    await transport.request("GET", "/test")
            
            # Should only be called once (no retries)
            assert call_count[0] == 1


class TestTransportCustomRetryConfig:
    """Tests for custom retry configuration"""

    @pytest.mark.asyncio
    async def test_custom_retryable_status_code(self):
        """Test custom retryable status codes"""
        retry_config = RetryConfig(retryable_statuses=[502, 503])
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return _create_response_mock(502, {"ok": False})
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config, retry_config=retry_config) as transport:
                response = await transport.request("GET", "/test", retry_config=retry_config)
                assert response["ok"] is True
                assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_custom_retry_config_override(self):
        """Test that custom retry config overrides defaults"""
        # Only one attempt (max_retries=0 means no retries)
        retry_config = RetryConfig(max_retries=0)
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            return _create_response_mock(500, {"ok": False})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config, retry_config=retry_config) as transport:
                # 500 is retryable by default, but we override with max_retries=0
                with pytest.raises(ApiError):
                    await transport.request("GET", "/test", retry_config=retry_config)
            
            # Should only be called once (no retries)
            assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_custom_retry_with_empty_statuses(self):
        """Test with empty retryable status codes"""
        # Empty retryable statuses means no status codes are retried
        retry_config = RetryConfig(retryable_statuses=[])
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            return _create_response_mock(500, {"ok": False})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config, retry_config=retry_config) as transport:
                # 500 is not retryable with empty list
                with pytest.raises(ApiError):
                    await transport.request("GET", "/test", retry_config=retry_config)
            
            # Should not retry (empty retryable statuses)
            assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_custom_retryable_exceptions(self):
        """Test custom retryable exceptions"""
        config = BotConfig(token="test_token")
        
        mock_client = MagicMock()
        call_count = [0]
        
        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise httpx.ConnectError("Connection error")
            return _create_response_mock(200, {"ok": True, "result": {}})
        
        mock_client.request = mock_request
        mock_client.aclose = AsyncMock()
        
        with patch('ymbot_async.transport.httpx_transport.httpx.AsyncClient', return_value=mock_client):
            async with HttpxTransport(config) as transport:
                response = await transport.request("GET", "/test")
                assert response["ok"] is True
                assert call_count[0] == 2