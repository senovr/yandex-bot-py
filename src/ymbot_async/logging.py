"""
Logging configuration for Yandex Messenger Bot Async Client
"""

import logging
import sys
from typing import Any, Literal, Protocol, runtime_checkable

try:
    import structlog

    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


@runtime_checkable
class LoggerProtocol(Protocol):
    """
    Protocol for logger instances that support kwargs.

    All logger methods must accept additional keyword arguments for context.
    """

    def debug(self, msg: str, **kwargs: Any) -> None: ...
    def info(self, msg: str, **kwargs: Any) -> None: ...
    def warning(self, msg: str, **kwargs: Any) -> None: ...
    def error(self, msg: str, **kwargs: Any) -> None: ...
    def critical(self, msg: str, **kwargs: Any) -> None: ...
    def exception(self, msg: str, **kwargs: Any) -> None: ...


def setup_logging(
    level: str = "INFO",
    format_type: Literal["json", "text"] = "text",
) -> None:
    """
    Setup logging for the library.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: Log format type (json or text)
    """
    if HAS_STRUCTLOG and format_type == "json":
        # Configure structlog for JSON output
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
        )
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=level,
        )
    else:
        # Standard text logging
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
            level=level,
        )


class KwargsLoggerWrapper:
    """
    Wrapper for standard logging.Logger that supports kwargs for context.

    This wrapper allows passing additional context via kwargs, which will be
    appended to the log message in a readable format.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _format_with_kwargs(self, msg: str, **kwargs: Any) -> str:
        """Format message with kwargs as additional context."""
        if not kwargs:
            return msg

        context_parts = [f"{k}={v}" for k, v in kwargs.items()]
        context = " | ".join(context_parts)
        return f"{msg} | {context}"

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._logger.debug(self._format_with_kwargs(msg, **kwargs))

    def info(self, msg: str, **kwargs: Any) -> None:
        self._logger.info(self._format_with_kwargs(msg, **kwargs))

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._logger.warning(self._format_with_kwargs(msg, **kwargs))

    def error(self, msg: str, **kwargs: Any) -> None:
        self._logger.error(self._format_with_kwargs(msg, **kwargs))

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._logger.critical(self._format_with_kwargs(msg, **kwargs))

    def exception(self, msg: str, **kwargs: Any) -> None:
        self._logger.exception(self._format_with_kwargs(msg, **kwargs))


def get_logger(name: str) -> LoggerProtocol:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance (structlog or standard logging with kwargs support)
    """
    if HAS_STRUCTLOG:
        # structlog loggers already support kwargs
        return structlog.get_logger(name)  # type: ignore[no-any-return]

    # Return wrapper for standard logging that supports kwargs
    return KwargsLoggerWrapper(logging.getLogger(name))


__all__ = ["setup_logging", "get_logger", "LoggerProtocol"]
