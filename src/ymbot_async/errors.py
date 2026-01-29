"""
Exception hierarchy for Yandex Messenger Bot Async Client
"""


class YMBotError(Exception):
    """Base exception for all library errors"""

    pass


class TransportError(YMBotError):
    """Network errors, timeouts, HTTP connection issues"""

    def __init__(self, message: str, retry_count: int = 0):
        self.retry_count = retry_count
        super().__init__(message)


class ApiError(YMBotError):
    """API errors (ok=false in response)"""

    def __init__(self, description: str, status_code: int | None = None):
        self.description = description
        self.status_code = status_code
        super().__init__(f"API Error: {description} (status: {status_code})")


class ValidationError(YMBotError):
    """Request validation errors"""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class OffsetError(YMBotError):
    """Offset management errors in polling"""

    pass


def assert_ok(response: dict) -> None:
    """
    Check that response has ok=true, raise ApiError if false.

    Args:
        response: API response dict

    Raises:
        ApiError: if response["ok"] is false or missing
    """
    if not response.get("ok"):
        raise ApiError(
            description=response.get("description", "Unknown error"),
            status_code=None,  # already handled in transport layer
        )
