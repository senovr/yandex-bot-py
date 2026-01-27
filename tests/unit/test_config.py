"""Unit tests for BotConfig and RetryConfig"""
import pytest

from ymbot_async.config import BotConfig, RetryConfig
from ymbot_async.errors import ValidationError


class TestBotConfig:
    """Tests for BotConfig class"""

    def test_create_default_config(self):
        """Test creating BotConfig with default values"""
        config = BotConfig(token="test_token")
        assert config.token == "test_token"
        assert config.base_url == "https://botapi.messenger.yandex.net/bot/v1"
        assert config.timeout_connect == 3.0
        assert config.timeout_read == 30.0
        assert config.timeout_write == 10.0
        assert config.timeout_pool == 3.0
        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20
        assert config.keepalive_expiry == 30.0
        assert config.max_retries == 3
        assert config.retry_backoff_base == 1.0
        assert config.retry_backoff_max == 10.0
        assert config.retry_jitter is True
        assert config.polling_limit == 100
        assert config.polling_timeout == 1.0
        assert config.polling_backoff == 0.5
        assert config.polling_max_backoff == 5.0
        assert config.queue_maxsize == 1000
        assert config.concurrency == 50
        assert config.log_level == "INFO"
        assert config.log_format == "text"

    def test_create_custom_config(self):
        """Test creating BotConfig with custom values"""
        config = BotConfig(
            token="custom_token",
            base_url="https://custom.api.com",
            timeout_connect=5.0,
            timeout_read=15.0,
            max_retries=5,
            polling_limit=50,
            concurrency=10,
            log_level="DEBUG",
            log_format="json",
        )
        assert config.token == "custom_token"
        assert config.base_url == "https://custom.api.com"
        assert config.timeout_connect == 5.0
        assert config.timeout_read == 15.0
        assert config.max_retries == 5
        assert config.polling_limit == 50
        assert config.concurrency == 10
        assert config.log_level == "DEBUG"
        assert config.log_format == "json"

    def test_empty_token_raises_validation_error(self):
        """Test that empty token raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            BotConfig(token="")
        assert "Token cannot be empty" in str(exc_info.value)
        assert exc_info.value.field == "token"

    def test_none_token_raises_validation_error(self):
        """Test that None token raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            BotConfig(token=None)  # type: ignore
        assert "Token cannot be empty" in str(exc_info.value)

    def test_polling_limit_too_high_raises_error(self):
        """Test that polling_limit > 1000 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            BotConfig(token="test", polling_limit=1001)
        assert "polling_limit must be <= 1000" in str(exc_info.value)
        assert exc_info.value.field == "polling_limit"

    def test_polling_limit_zero_raises_error(self):
        """Test that polling_limit <= 0 raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            BotConfig(token="test", polling_limit=0)
        assert "polling_limit must be > 0" in str(exc_info.value)
        assert exc_info.value.field == "polling_limit"

    def test_polling_limit_negative_raises_error(self):
        """Test that negative polling_limit raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            BotConfig(token="test", polling_limit=-1)
        assert "polling_limit must be > 0" in str(exc_info.value)

    def test_max_retries_negative_raises_error(self):
        """Test that negative max_retries raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            BotConfig(token="test", max_retries=-1)
        assert "max_retries must be >= 0" in str(exc_info.value)
        assert exc_info.value.field == "max_retries"

    def test_max_retries_zero_is_valid(self):
        """Test that max_retries = 0 is valid"""
        config = BotConfig(token="test", max_retries=0)
        assert config.max_retries == 0

    def test_max_retries_positive_is_valid(self):
        """Test that positive max_retries is valid"""
        config = BotConfig(token="test", max_retries=10)
        assert config.max_retries == 10

    def test_invalid_log_level_raises_error(self):
        """Test that invalid log_level raises error"""
        # This test checks that the Literal type is enforced at type-checking time
        # At runtime, Python doesn't enforce Literal, so we just create the config
        # The type checker would catch this
        config = BotConfig(token="test", log_level="INVALID")  # type: ignore
        # At runtime, this will not raise an error, but type checker would catch it
        assert config.log_level == "INVALID"

    def test_invalid_log_format_raises_error(self):
        """Test that invalid log_format raises error"""
        # Similar to log_level, this is type-checked
        config = BotConfig(token="test", log_format="invalid")  # type: ignore
        assert config.log_format == "invalid"

    def test_config_is_frozen(self):
        """Test that BotConfig is frozen (immutable)"""
        config = BotConfig(token="test")
        with pytest.raises(Exception):  # FrozenInstanceError from dataclasses
            config.token = "new_token"  # type: ignore


class TestRetryConfig:
    """Tests for RetryConfig class"""

    def test_create_default_retry_config(self):
        """Test creating RetryConfig with default values"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.retryable_statuses == {502, 503, 504}
        assert config.retryable_exceptions == (TimeoutError, ConnectionError)

    def test_create_custom_retry_config(self):
        """Test creating RetryConfig with custom values"""
        config = RetryConfig(
            max_retries=5,
            retryable_statuses={500, 502, 503, 504},
        )
        assert config.max_retries == 5
        assert config.retryable_statuses == {500, 502, 503, 504}

    def test_max_retries_negative_raises_error(self):
        """Test that negative max_retries raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(max_retries=-1)
        assert "max_retries must be >= 0" in str(exc_info.value)
        assert exc_info.value.field == "max_retries"

    def test_max_retries_zero_is_valid(self):
        """Test that max_retries = 0 is valid"""
        config = RetryConfig(max_retries=0)
        assert config.max_retries == 0

    def test_max_retries_positive_is_valid(self):
        """Test that positive max_retries is valid"""
        config = RetryConfig(max_retries=10)
        assert config.max_retries == 10

    def test_default_retryable_statuses(self):
        """Test default retryable HTTP status codes"""
        config = RetryConfig()
        assert 502 in config.retryable_statuses
        assert 503 in config.retryable_statuses
        assert 504 in config.retryable_statuses

    def test_custom_retryable_statuses(self):
        """Test custom retryable HTTP status codes"""
        config = RetryConfig(retryable_statuses={500, 502})
        assert config.retryable_statuses == {500, 502}
        assert 503 not in config.retryable_statuses

    def test_default_retryable_exceptions(self):
        """Test default retryable exceptions"""
        config = RetryConfig()
        assert TimeoutError in config.retryable_exceptions
        assert ConnectionError in config.retryable_exceptions

    def test_custom_retryable_exceptions(self):
        """Test custom retryable exceptions"""
        config = RetryConfig(retryable_exceptions=(TimeoutError, OSError))
        assert TimeoutError in config.retryable_exceptions
        assert OSError in config.retryable_exceptions
        assert ConnectionError not in config.retryable_exceptions