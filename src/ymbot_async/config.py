"""
Configuration classes for Yandex Messenger Bot Async Client
"""

from dataclasses import dataclass, field
from typing import Literal

from ymbot_async.errors import ValidationError


@dataclass(frozen=True)
class BotConfig:
    """
    Bot configuration with production-safe defaults.
    
    Attributes:
        token: OAuth token for Yandex Bot API
        base_url: Base URL for API (default: official Yandex endpoint)
        timeout_connect: Connection timeout in seconds
        timeout_read: Read timeout in seconds
        timeout_write: Write timeout in seconds
        timeout_pool: Pool acquisition timeout in seconds
        max_connections: Maximum connections in pool
        max_keepalive_connections: Maximum keepalive connections
        keepalive_expiry: Keepalive expiry time in seconds
        max_retries: Maximum retry attempts for failed requests
        retry_backoff_base: Base for exponential backoff
        retry_backoff_max: Maximum backoff time in seconds
        retry_jitter: Add random jitter to backoff
        polling_limit: Maximum updates per getUpdates call (max 1000)
        polling_timeout: Delay in seconds when no updates
        polling_backoff: Multiplier for consecutive empty responses
        polling_max_backoff: Maximum backoff time in seconds for empty responses
        queue_maxsize: Maximum size of update queue
        concurrency: Maximum concurrent handlers running
        log_level: Logging level
        log_format: Log format (json or text)
    """

    token: str
    base_url: str = "https://botapi.messenger.yandex.net/bot/v1"

    # Timeout settings
    timeout_connect: float = 3.0
    timeout_read: float = 30.0
    timeout_write: float = 10.0
    timeout_pool: float = 3.0

    # Connection pool settings
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0

    # Retry settings
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    retry_backoff_max: float = 10.0
    retry_jitter: bool = True

    # Polling settings
    polling_limit: int = 100
    polling_timeout: float = 1.0
    polling_backoff: float = 0.5
    polling_max_backoff: float = 5.0

    # Dispatcher settings
    queue_maxsize: int = 1000
    concurrency: int = 50

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "text"

    def __post_init__(self) -> None:
        """Validate configuration after initialization"""
        if not self.token:
            raise ValidationError("Token cannot be empty", field="token")
        if self.polling_limit > 1000:
            raise ValidationError(
                "polling_limit must be <= 1000", field="polling_limit"
            )
        if self.polling_limit <= 0:
            raise ValidationError(
                "polling_limit must be > 0", field="polling_limit"
            )
        if self.max_retries < 0:
            raise ValidationError(
                "max_retries must be >= 0", field="max_retries"
            )


@dataclass
class RetryConfig:
    """
    Retry configuration for individual requests.
    
    Attributes:
        max_retries: Maximum retry attempts
        retryable_statuses: HTTP status codes to retry
        retryable_exceptions: Exception types to retry
    """

    max_retries: int = 3
    retryable_statuses: set[int] = field(
        default_factory=lambda: {502, 503, 504}
    )
    # Include httpx exceptions for retry on timeout and network errors
    retryable_exceptions: tuple[type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
        # httpx exceptions (imported dynamically to avoid hard dependency)
    )

    def __post_init__(self) -> None:
        """Validate retry configuration"""
        if self.max_retries < 0:
            raise ValidationError(
                "max_retries must be >= 0", field="max_retries"
            )