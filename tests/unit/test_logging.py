"""Unit tests for logging module"""

import logging
import sys
from io import StringIO

import pytest

from ymbot_async.logging import (
    HAS_STRUCTLOG,
    KwargsLoggerWrapper,
    LoggerProtocol,
    get_logger,
    setup_logging,
)


class TestSetupLogging:
    """Tests for setup_logging function"""

    def test_setup_logging_json_format_fallback(self):
        """Test setup_logging with json format falls back to text when structlog not available"""
        if HAS_STRUCTLOG:
            pytest.skip("structlog is available")

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Should fall back to text format
            setup_logging(level="WARNING", format_type="json")

            # Just verify it doesn't crash
            assert True
        finally:
            sys.stdout = old_stdout


class TestKwargsLoggerWrapper:
    """Tests for KwargsLoggerWrapper"""

    def test_wrapper_initializes_with_logger(self):
        """Test wrapper initializes with standard logger"""
        base_logger = logging.getLogger("test_wrapper")
        wrapper = KwargsLoggerWrapper(base_logger)

        assert wrapper._logger == base_logger

    def test_wrapper_debug_without_kwargs(self, caplog):
        """Test wrapper debug without kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_debug")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.DEBUG):
            wrapper.debug("Debug message")

        assert len(caplog.records) == 1
        assert "Debug message" in caplog.text

    def test_wrapper_debug_with_kwargs(self, caplog):
        """Test wrapper debug with kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_debug_kwargs")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.DEBUG):
            wrapper.debug("Debug message", key1="value1", key2="value2")

        assert len(caplog.records) == 1
        assert "Debug message" in caplog.text
        assert "key1=value1" in caplog.text
        assert "key2=value2" in caplog.text

    def test_wrapper_info_without_kwargs(self, caplog):
        """Test wrapper info without kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_info")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.INFO):
            wrapper.info("Info message")

        assert len(caplog.records) == 1
        assert "Info message" in caplog.text

    def test_wrapper_info_with_kwargs(self, caplog):
        """Test wrapper info with kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_info_kwargs")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.INFO):
            wrapper.info("Info message", user_id="123", action="login")

        assert len(caplog.records) == 1
        assert "Info message" in caplog.text
        assert "user_id=123" in caplog.text
        assert "action=login" in caplog.text

    def test_wrapper_warning_without_kwargs(self, caplog):
        """Test wrapper warning without kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_warning")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.WARNING):
            wrapper.warning("Warning message")

        assert len(caplog.records) == 1
        assert "Warning message" in caplog.text

    def test_wrapper_warning_with_kwargs(self, caplog):
        """Test wrapper warning with kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_warning_kwargs")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.WARNING):
            wrapper.warning("Warning message", code=404, resource="user")

        assert len(caplog.records) == 1
        assert "Warning message" in caplog.text
        assert "code=404" in caplog.text
        assert "resource=user" in caplog.text

    def test_wrapper_error_without_kwargs(self, caplog):
        """Test wrapper error without kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_error")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.ERROR):
            wrapper.error("Error message")

        assert len(caplog.records) == 1
        assert "Error message" in caplog.text

    def test_wrapper_error_with_kwargs(self, caplog):
        """Test wrapper error with kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_error_kwargs")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.ERROR):
            wrapper.error("Error message", error_code=500, detail="Internal error")

        assert len(caplog.records) == 1
        assert "Error message" in caplog.text
        assert "error_code=500" in caplog.text
        assert "detail=Internal error" in caplog.text

    def test_wrapper_critical_without_kwargs(self, caplog):
        """Test wrapper critical without kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_critical")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.CRITICAL):
            wrapper.critical("Critical message")

        assert len(caplog.records) == 1
        assert "Critical message" in caplog.text

    def test_wrapper_critical_with_kwargs(self, caplog):
        """Test wrapper critical with kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_critical_kwargs")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.CRITICAL):
            wrapper.critical("Critical message", system="database", status="down")

        assert len(caplog.records) == 1
        assert "Critical message" in caplog.text
        assert "system=database" in caplog.text
        assert "status=down" in caplog.text

    def test_wrapper_exception_without_kwargs(self, caplog):
        """Test wrapper exception without kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_exception")
        wrapper = KwargsLoggerWrapper(base_logger)

        try:
            raise ValueError("Test exception")
        except Exception:
            with caplog.at_level(logging.ERROR):
                wrapper.exception("Exception occurred")

        assert len(caplog.records) == 1
        assert "Exception occurred" in caplog.text
        assert "ValueError: Test exception" in caplog.text

    def test_wrapper_exception_with_kwargs(self, caplog):
        """Test wrapper exception with kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_exception_kwargs")
        wrapper = KwargsLoggerWrapper(base_logger)

        try:
            raise ValueError("Test exception")
        except Exception:
            with caplog.at_level(logging.ERROR):
                wrapper.exception("Exception occurred", error_type="ValueError", context="test")

        assert len(caplog.records) == 1
        assert "Exception occurred" in caplog.text
        assert "error_type=ValueError" in caplog.text
        assert "context=test" in caplog.text
        assert "ValueError: Test exception" in caplog.text

    def test_wrapper_formats_single_kwarg(self, caplog):
        """Test wrapper formats single kwarg correctly"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_single_kwarg")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.INFO):
            wrapper.info("Message", key="value")

        assert "Message | key=value" in caplog.text

    def test_wrapper_formats_multiple_kwargs(self, caplog):
        """Test wrapper formats multiple kwargs correctly"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_multiple_kwargs")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.INFO):
            wrapper.info("Message", a=1, b=2, c=3)

        # Check all kwargs are present (order may vary)
        assert "a=1" in caplog.text
        assert "b=2" in caplog.text
        assert "c=3" in caplog.text

    def test_wrapper_formats_special_characters(self, caplog):
        """Test wrapper handles special characters in kwargs"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        base_logger = logging.getLogger("test_special_chars")
        wrapper = KwargsLoggerWrapper(base_logger)

        with caplog.at_level(logging.INFO):
            wrapper.info("Message", text="hello world", code="CODE-123")

        assert "text=hello world" in caplog.text
        assert "code=CODE-123" in caplog.text


class TestGetLogger:
    """Tests for get_logger function"""

    def test_get_logger_returns_logger_protocol(self):
        """Test get_logger returns LoggerProtocol instance"""
        logger = get_logger("test_logger")

        # Should conform to protocol
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")
        assert hasattr(logger, "exception")

    def test_get_logger_with_structlog(self):
        """Test get_logger with structlog available"""
        if not HAS_STRUCTLOG:
            pytest.skip("structlog not available")

        logger = get_logger("test_structlog_logger")

        # structlog loggers should support kwargs
        logger.info("Message", key="value")  # Should not raise

    def test_get_logger_without_structlog(self):
        """Test get_logger without structlog uses wrapper"""
        if HAS_STRUCTLOG:
            pytest.skip("structlog is available")

        logger = get_logger("test_standard_logger")

        # Should be wrapped
        assert isinstance(logger, KwargsLoggerWrapper)

    def test_get_logger_same_name_returns_same_instance(self):
        """Test get_logger returns same instance for same name"""
        logger1 = get_logger("test_same_logger")
        logger2 = get_logger("test_same_logger")

        # Should be same logger instance
        if hasattr(logger1, "_logger") and hasattr(logger2, "_logger"):
            assert logger1._logger is logger2._logger
        else:
            # For structlog loggers
            assert logger1 is logger2

    def test_get_logger_different_name_returns_different_instance(self):
        """Test get_logger returns different instance for different name"""
        if HAS_STRUCTLOG:
            pytest.skip("structlog loggers use lazy proxy pattern without _logger attribute")
        logger1 = get_logger("test_different_logger_1")
        logger2 = get_logger("test_different_logger_2")

        # Should be different loggers
        if hasattr(logger1, "_logger") and hasattr(logger2, "_logger"):
            assert logger1._logger is not logger2._logger
        else:
            # For structlog loggers
            assert logger1 is not logger2

    def test_get_logger_logs_correctly(self, caplog):
        """Test get_logger logs correctly"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        logger = get_logger("test_logging_logger")

        with caplog.at_level(logging.INFO):
            logger.info("Test message", key="value")

        assert len(caplog.records) == 1
        assert "Test message" in caplog.text


class TestLoggerProtocol:
    """Tests for LoggerProtocol"""

    def test_kwargs_logger_conforms_to_protocol(self):
        """Test KwargsLoggerWrapper conforms to LoggerProtocol"""
        base_logger = logging.getLogger("test_protocol")
        wrapper = KwargsLoggerWrapper(base_logger)

        # Should conform to protocol
        assert isinstance(wrapper, LoggerProtocol)

    def test_standard_logger_conformance_check(self):
        """Test standard Logger protocol conformance"""
        base_logger = logging.getLogger("test_no_protocol")

        # Standard logger does not support kwargs, but has same method names
        # This test just verifies the logger exists
        assert base_logger is not None


class TestLoggingIntegration:
    """Integration tests for logging module"""

    def test_full_logging_flow(self, caplog):
        """Test full logging flow from setup to output"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        import logging

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Setup logging
            setup_logging(level="INFO", format_type="text")

            # Get logger
            logger = get_logger("test_flow")

            # IMPORTANT: Use caplog to capture logs at INFO level
            with caplog.at_level(logging.INFO):
                # Log at different levels
                logger.debug("Debug message", level="DEBUG")  # Should not appear
                logger.info("Info message", level="INFO")
                logger.warning("Warning message", level="WARNING")
                logger.error("Error message", level="ERROR")

            # Check output
            assert "Info message" in caplog.text
            assert "Warning message" in caplog.text
            assert "Error message" in caplog.text
            assert "Debug message" not in caplog.text
            assert "level=INFO" in caplog.text
            assert "level=WARNING" in caplog.text
            assert "level=ERROR" in caplog.text
        finally:
            sys.stdout = old_stdout

    def test_multiple_loggers_independent(self, caplog):
        """Test multiple loggers are independent"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        setup_logging(level="DEBUG", format_type="text")

        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")

        with caplog.at_level(logging.DEBUG):
            logger1.info("From logger1", id=1)
            logger2.info("From logger2", id=2)

        assert "From logger1" in caplog.text
        assert "From logger2" in caplog.text
        assert "id=1" in caplog.text
        assert "id=2" in caplog.text

    def test_logger_with_exception(self, caplog):
        """Test logger with exception context"""
        if HAS_STRUCTLOG:
            pytest.skip("caplog doesn't capture structlog logs")
        logger = get_logger("test_exception_flow")

        try:
            raise ValueError("Test error")
        except Exception:
            with caplog.at_level(logging.ERROR):
                logger.exception("An error occurred", error_id="123")

        assert "An error occurred" in caplog.text
        assert "error_id=123" in caplog.text
        assert "ValueError: Test error" in caplog.text
