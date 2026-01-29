"""
Async HTTP transport using httpx with retry logic
"""

from __future__ import annotations

import asyncio
import random
import types
from typing import Any, Literal

import httpx

from ymbot_async.config import BotConfig, RetryConfig
from ymbot_async.errors import ApiError, TransportError
from ymbot_async.logging import LoggerProtocol, get_logger

logger: LoggerProtocol = get_logger(__name__)


class HttpxTransport:
    """
    Async HTTP transport with retry and timeout support.

    Manages httpx.AsyncClient lifecycle and implements exponential backoff
    retry logic for transient failures.
    """

    def __init__(
        self,
        config: BotConfig,
        retry_config: RetryConfig | None = None,
    ):
        """
        Initialize transport.

        Args:
            config: Bot configuration
            retry_config: Retry configuration (uses default if None)
        """
        self.config = config
        self.retry_config = retry_config or RetryConfig()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HttpxTransport:
        """Enter async context and create HTTP client."""
        timeout = httpx.Timeout(
            connect=self.config.timeout_connect,
            read=self.config.timeout_read,
            write=self.config.timeout_write,
            pool=self.config.timeout_pool,
        )
        limits = httpx.Limits(
            max_connections=self.config.max_connections,
            max_keepalive_connections=self.config.max_keepalive_connections,
            keepalive_expiry=self.config.keepalive_expiry,
        )
        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            base_url=self.config.base_url,
            verify=True,  # SSL verify
        )
        logger.info(
            "HTTP client created",
            base_url=self.config.base_url,
            max_connections=self.config.max_connections,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit async context and close HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info("HTTP client closed")
            self._client = None

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff with optional jitter.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Backoff delay in seconds
        """
        backoff = self.config.retry_backoff_base * (2**attempt)
        backoff = min(backoff, self.config.retry_backoff_max)

        if self.config.retry_jitter:
            jitter = backoff * 0.1  # 10% jitter
            backoff = backoff + random.uniform(-jitter, jitter)  # nosec B311

        return float(max(backoff, 0.0))

    async def request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        retry_config: RetryConfig | None = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET or POST)
            path: API endpoint path
            json: JSON body for POST requests
            params: Query parameters for GET requests
            headers: Additional headers
            retry_config: Override retry config for this request

        Returns:
            Parsed JSON response

        Raises:
            TransportError: If request fails after retries
            ApiError: If API returns error response
        """
        retry_cfg = retry_config or self.retry_config
        last_error: Exception | None = None

        for attempt in range(retry_cfg.max_retries + 1):
            try:
                if not self._client:
                    # Client not initialized - raise immediately without retries
                    raise TransportError(
                        "HTTP client not initialized. Use async with statement.",
                    )

                # Build headers with authorization
                request_headers = {"Authorization": f"OAuth {self.config.token}"}
                if headers:
                    request_headers.update(headers)

                response = await self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                    headers=request_headers,
                )

                # Check for retryable status codes
                if (
                    response.status_code in retry_cfg.retryable_statuses
                    and attempt < retry_cfg.max_retries
                ):
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        "Retryable status code",
                        status_code=response.status_code,
                        attempt=attempt + 1,
                        max_retries=retry_cfg.max_retries,
                        backoff=round(backoff, 2),
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Parse JSON response
                try:
                    response_data = response.json()
                    if not isinstance(response_data, dict):
                        raise TransportError("Expected dict response from API")
                except Exception as e:
                    raise TransportError(
                        f"Failed to parse JSON response: {e}",
                    ) from e

                # Check for API errors
                if not response_data.get("ok"):
                    raise ApiError(
                        description=response_data.get("description", "Unknown error"),
                        status_code=response.status_code,
                    )

                # Log successful request
                logger.debug(
                    "Request successful",
                    method=method,
                    path=path,
                    status_code=response.status_code,
                )

                return response_data

            except ApiError as e:
                # Check if this API error has a retryable status code
                if e.status_code in retry_cfg.retryable_statuses:
                    if attempt < retry_cfg.max_retries:
                        backoff = self._calculate_backoff(attempt)
                        logger.warning(
                            "Retryable API error",
                            status_code=e.status_code,
                            description=e.description,
                            attempt=attempt + 1,
                            max_retries=retry_cfg.max_retries,
                            backoff=round(backoff, 2),
                        )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        logger.error(
                            "Max retries exceeded for API error",
                            status_code=e.status_code,
                            description=e.description,
                            max_retries=retry_cfg.max_retries,
                        )
                # Non-retryable API errors are raised immediately
                raise

            except TransportError as e:
                # Check if this is a client not initialized error - not retryable
                if "HTTP client not initialized" in str(e):
                    raise
                # Other TransportErrors are retryable
                last_error = e
                if attempt < retry_cfg.max_retries:
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        "Retryable exception",
                        exception_type=type(e).__name__,
                        exception_message=str(e),
                        attempt=attempt + 1,
                        max_retries=retry_cfg.max_retries,
                        backoff=round(backoff, 2),
                    )
                    await asyncio.sleep(backoff)
                    continue
                else:
                    logger.error(
                        "Max retries exceeded",
                        exception_type=type(e).__name__,
                        exception_message=str(e),
                        max_retries=retry_cfg.max_retries,
                    )

            except Exception as e:
                # Check if this is retryable
                is_retryable = isinstance(e, tuple(retry_cfg.retryable_exceptions))

                # Also check for httpx-specific exceptions (network/timeouts)
                if not is_retryable:
                    # httpx timeout exceptions
                    is_retryable = isinstance(
                        e,
                        (
                            httpx.TimeoutException,  # Base class for all timeouts
                            httpx.ConnectTimeout,
                            httpx.ReadTimeout,
                            httpx.WriteTimeout,
                            httpx.PoolTimeout,
                        ),
                    )

                # Check for httpx network errors
                if not is_retryable:
                    is_retryable = isinstance(
                        e,
                        (
                            httpx.ConnectError,
                            httpx.NetworkError,  # Base class for network errors
                            httpx.ProtocolError,
                        ),
                    )

                if is_retryable:
                    # Retryable exception
                    last_error = e
                    if attempt < retry_cfg.max_retries:
                        backoff = self._calculate_backoff(attempt)
                        logger.warning(
                            "Retryable exception",
                            exception_type=type(e).__name__,
                            exception_message=str(e),
                            attempt=attempt + 1,
                            max_retries=retry_cfg.max_retries,
                            backoff=round(backoff, 2),
                        )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        logger.error(
                            "Max retries exceeded",
                            exception_type=type(e).__name__,
                            exception_message=str(e),
                            max_retries=retry_cfg.max_retries,
                        )
                else:
                    # Unexpected errors are not retryable
                    logger.error(
                        "Unexpected exception in request",
                        exception_type=type(e).__name__,
                        exception_message=str(e),
                    )
                    raise TransportError(f"Unexpected error: {e}") from e

        # If we get here, all retries failed
        raise TransportError(
            f"Request failed after {retry_cfg.max_retries} retries",
            retry_count=retry_cfg.max_retries,
        ) from last_error

    async def request_json(
        self,
        method: Literal["GET", "POST"],
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Convenience method for JSON requests.

        Args:
            method: HTTP method (GET or POST)
            path: API endpoint path
            json: JSON body for POST requests
            params: Query parameters for GET requests
            headers: Additional headers

        Returns:
            Parsed JSON response
        """
        return await self.request(
            method=method,
            path=path,
            json=json,
            params=params,
            headers=headers,
        )
