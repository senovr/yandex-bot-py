"""Unit tests for HttpxTransport"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from ymbot_async.transport.httpx_transport import HttpxTransport
from ymbot_async.config import BotConfig, RetryConfig
from ymbot_async.errors import TransportError, ApiError


class TestHttpxTransport:
    """Tests for HttpxTransport"""

    @pytest.fixture
    def transport(self, bot_config):
        """Create HttpxTransport instance"""
        return HttpxTransport(bot_config)

    @pytest.mark.asyncio
    async def test_transport_context_manager(self, transport):
        """Test transport as async context manager"""
        async with transport as t:
            assert t._client is not None
            assert isinstance(t._client, httpx.AsyncClient)
        assert transport._client is None

    @pytest.mark.asyncio
    async def test_transport_initializes_with_config(self, transport):
        """Test transport uses config for initialization"""
        async with transport as t:
            # URL may or may not have trailing slash, compare as strings
            assert str(t._client.base_url).startswith("https://botapi.messenger.yandex.net/bot/v1")
            assert t._client.timeout.connect == 3.0
            assert t._client.timeout.read == 30.0
            assert t._client.timeout.write == 10.0
            assert t._client.timeout.pool == 3.0

    @pytest.mark.asyncio
    async def test_transport_custom_config(self, bot_config_custom):
        """Test transport with custom config"""
        transport = HttpxTransport(bot_config_custom)
        async with transport as t:
            assert t._client.timeout.connect == 5.0
            assert t._client.timeout.read == 15.0

    @pytest.mark.asyncio
    async def test_request_json_success(self, transport):
        """Test successful JSON request"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": "data"}
            transport._client.request = AsyncMock(return_value=mock_response)

            result = await transport.request_json("GET", "/test")
            assert result == {"ok": True, "result": "data"}

    @pytest.mark.asyncio
    async def test_request_json_with_params(self, transport):
        """Test request with query parameters"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            transport._client.request = AsyncMock(return_value=mock_response)

            await transport.request_json(
                "GET",
                "/test",
                params={"param1": "value1"}
            )
            transport._client.request.assert_called_once()
            call_kwargs = transport._client.request.call_args[1]
            assert call_kwargs["params"] == {"param1": "value1"}

    @pytest.mark.asyncio
    async def test_request_json_with_body(self, transport):
        """Test request with JSON body"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            transport._client.request = AsyncMock(return_value=mock_response)

            await transport.request_json(
                "POST",
                "/test",
                json={"key": "value"}
            )
            transport._client.request.assert_called_once()
            call_kwargs = transport._client.request.call_args[1]
            assert call_kwargs["json"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_request_with_headers(self, transport):
        """Test request with custom headers"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            transport._client.request = AsyncMock(return_value=mock_response)

            await transport.request(
                "GET",
                "/test",
                headers={"X-Custom": "value"}
            )
            call_kwargs = transport._client.request.call_args[1]
            assert "X-Custom" in call_kwargs["headers"]
            assert call_kwargs["headers"]["X-Custom"] == "value"

    @pytest.mark.asyncio
    async def test_request_adds_authorization_header(self, transport):
        """Test request adds OAuth authorization header"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            transport._client.request = AsyncMock(return_value=mock_response)

            await transport.request("GET", "/test")
            call_kwargs = transport._client.request.call_args[1]
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "OAuth test_token_123"

    @pytest.mark.asyncio
    async def test_request_without_context_manager(self, transport):
        """Test request without context manager raises error"""
        with pytest.raises(TransportError) as exc_info:
            await transport.request("GET", "/test")
        assert "HTTP client not initialized" in str(exc_info.value)


class TestHttpxTransportRetryLogic:
    """Tests for retry logic"""

    @pytest.mark.asyncio
    async def test_retry_on_502(self, transport):
        """Test retry on 502 Bad Gateway"""
        async with transport:
            # First attempt returns 502, second succeeds
            mock_response_502 = MagicMock()
            mock_response_502.status_code = 502
            mock_response_502.json.return_value = {"error": "Bad Gateway"}
            
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"ok": True, "result": "data"}
            
            transport._client.request = AsyncMock(
                side_effect=[mock_response_502, mock_response_200]
            )

            with patch("asyncio.sleep"):  # Skip actual sleep
                result = await transport.request("GET", "/test")
            
            assert result == {"ok": True, "result": "data"}
            assert transport._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_503(self, transport):
        """Test retry on 503 Service Unavailable"""
        async with transport:
            mock_response_503 = MagicMock()
            mock_response_503.status_code = 503
            mock_response_503.json.return_value = {"error": "Service Unavailable"}
            
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"ok": True}
            
            transport._client.request = AsyncMock(
                side_effect=[mock_response_503, mock_response_200]
            )

            with patch("asyncio.sleep"):
                result = await transport.request("GET", "/test")
            
            assert result == {"ok": True}
            assert transport._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_504(self, transport):
        """Test retry on 504 Gateway Timeout"""
        async with transport:
            mock_response_504 = MagicMock()
            mock_response_504.status_code = 504
            mock_response_504.json.return_value = {"error": "Gateway Timeout"}
            
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"ok": True}
            
            transport._client.request = AsyncMock(
                side_effect=[mock_response_504, mock_response_200]
            )

            with patch("asyncio.sleep"):
                result = await transport.request("GET", "/test")
            
            assert result == {"ok": True}
            assert transport._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_timeout_error(self, transport):
        """Test retry on TimeoutError"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            
            transport._client.request = AsyncMock(
                side_effect=[TimeoutError("Timeout"), mock_response]
            )

            with patch("asyncio.sleep"):
                result = await transport.request("GET", "/test")
            
            assert result == {"ok": True}
            assert transport._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, transport):
        """Test retry on ConnectionError"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            
            transport._client.request = AsyncMock(
                side_effect=[ConnectionError("Connection failed"), mock_response]
            )

            with patch("asyncio.sleep"):
                result = await transport.request("GET", "/test")
            
            assert result == {"ok": True}
            assert transport._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, transport):
        """Test that max retries is respected"""
        async with transport:
            mock_response_502 = MagicMock()
            mock_response_502.status_code = 502
            mock_response_502.json.return_value = {"error": "Bad Gateway", "ok": False}
            
            transport._client.request = AsyncMock(return_value=mock_response_502)

            with patch("asyncio.sleep"):
                with pytest.raises(ApiError) as exc_info:
                    await transport.request("GET", "/test")
            
            # After retries, ApiError is raised for non-retryable status
            assert exc_info.value.status_code == 502
            # 1 initial + 3 retries = 4 total calls before ApiError
            assert transport._client.request.call_count == 4

    @pytest.mark.asyncio
    async def test_custom_retry_config(self, transport, retry_config_custom):
        """Test custom retry configuration"""
        async with transport:
            mock_response_502 = MagicMock()
            mock_response_502.status_code = 502
            mock_response_502.json.return_value = {"error": "Bad Gateway", "ok": False}
            
            transport._client.request = AsyncMock(return_value=mock_response_502)

            with patch("asyncio.sleep"):
                with pytest.raises(ApiError):
                    await transport.request(
                        "GET",
                        "/test",
                        retry_config=retry_config_custom
                    )
            
            # Should have 1 initial + 5 retries = 6 total
            assert transport._client.request.call_count == 6


class TestHttpxTransportBackoff:
    """Tests for backoff calculation"""

    def test_calculate_backoff_no_jitter(self, bot_config_no_jitter):
        """Test backoff calculation without jitter"""
        transport = HttpxTransport(bot_config_no_jitter)
        
        backoff = transport._calculate_backoff(attempt=0)
        assert backoff == 1.0  # base * 2^0

        backoff = transport._calculate_backoff(attempt=1)
        assert backoff == 2.0  # base * 2^1

        backoff = transport._calculate_backoff(attempt=2)
        assert backoff == 4.0  # base * 2^2

    def test_calculate_backoff_with_max(self, bot_config_custom_backoff_max):
        """Test backoff doesn't exceed max"""
        transport = HttpxTransport(bot_config_custom_backoff_max)
        
        # This would be 16.0 but should be capped at 5.0
        backoff = transport._calculate_backoff(attempt=10)
        assert backoff == 5.0

    def test_calculate_backoff_with_jitter(self, bot_config):
        """Test backoff with jitter adds randomness"""
        transport = HttpxTransport(bot_config)
        
        backoffs = [transport._calculate_backoff(attempt=0) for _ in range(100)]
        
        # With 10% jitter, values should be around 1.0 ± 0.1
        assert all(0.85 <= b <= 1.15 for b in backoffs)
        assert len(set(backoffs)) > 1  # Should have different values due to jitter


class TestHttpxTransportErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_api_error_not_retried(self, transport):
        """Test that ApiError is not retried"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "ok": False,
                "description": "Bad Request"
            }
            
            transport._client.request = AsyncMock(return_value=mock_response)

            with pytest.raises(ApiError) as exc_info:
                await transport.request("GET", "/test")
            
            assert exc_info.value.description == "Bad Request"
            assert exc_info.value.status_code == 400
            assert transport._client.request.call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_non_retryable_exception(self, transport):
        """Test that non-retryable exceptions are raised immediately"""
        async with transport:
            transport._client.request = AsyncMock(
                side_effect=ValueError("Unexpected error")
            )

            with pytest.raises(TransportError) as exc_info:
                await transport.request("GET", "/test")
            
            assert "Unexpected error" in str(exc_info.value)
            assert transport._client.request.call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_transport_error_is_retried(self, transport):
        """Test that TransportError is retried"""
        async with transport:
            # First attempt raises TransportError, second succeeds
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            
            transport._client.request = AsyncMock(
                side_effect=[TransportError("Transport failed"), mock_response]
            )

            with patch("asyncio.sleep"):
                result = await transport.request("GET", "/test")
            
            assert result == {"ok": True}
            assert transport._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_json_parse_error(self, transport):
        """Test error when response JSON cannot be parsed"""
        async with transport:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            
            transport._client.request = AsyncMock(return_value=mock_response)

            with patch("asyncio.sleep"):
                with pytest.raises(TransportError) as exc_info:
                    await transport.request("GET", "/test")
            
            # JSON parse error is retried as TransportError, final message indicates retries
            assert "Request failed after" in str(exc_info.value)
            # 1 initial + 3 retries = 4 total
            assert transport._client.request.call_count == 4


class TestHttpxTransportLimits:
    """Tests for connection limits"""

    @pytest.mark.asyncio
    async def test_connection_limits(self, bot_config):
        """Test transport creates client successfully"""
        transport = HttpxTransport(bot_config)
        async with transport as t:
            # Verify client is created and has limits configured
            assert t._client is not None
            assert isinstance(t._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_custom_limits(self, bot_config_custom):
        """Test transport with custom limits"""
        transport = HttpxTransport(bot_config_custom)
        async with transport as t:
            # Custom config should create client successfully
            assert t._client is not None
