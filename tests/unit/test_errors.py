"""Unit tests for error classes"""
import pytest

from ymbot_async.errors import (
    YMBotError,
    TransportError,
    ApiError,
    ValidationError,
    OffsetError,
    assert_ok,
)


class TestYMBotError:
    """Tests for base YMBotError class"""

    def test_create_base_error(self):
        """Test creating base YMBotError"""
        error = YMBotError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_raise_base_error(self):
        """Test raising YMBotError"""
        with pytest.raises(YMBotError) as exc_info:
            raise YMBotError("Test error")
        assert str(exc_info.value) == "Test error"


class TestTransportError:
    """Tests for TransportError class"""

    def test_create_transport_error(self):
        """Test creating TransportError with message only"""
        error = TransportError("Network timeout")
        assert str(error) == "Network timeout"
        assert error.retry_count == 0
        assert isinstance(error, YMBotError)

    def test_create_transport_error_with_retry_count(self):
        """Test creating TransportError with retry count"""
        error = TransportError("Network timeout", retry_count=3)
        assert str(error) == "Network timeout"
        assert error.retry_count == 3

    def test_transport_error_retry_count_default(self):
        """Test that default retry_count is 0"""
        error = TransportError("Test")
        assert error.retry_count == 0

    def test_transport_error_with_high_retry_count(self):
        """Test TransportError with high retry count"""
        error = TransportError("Failed", retry_count=10)
        assert error.retry_count == 10

    def test_raise_transport_error(self):
        """Test raising TransportError"""
        with pytest.raises(TransportError) as exc_info:
            raise TransportError("Connection failed", retry_count=2)
        assert str(exc_info.value) == "Connection failed"
        assert exc_info.value.retry_count == 2


class TestApiError:
    """Tests for ApiError class"""

    def test_create_api_error_with_description_only(self):
        """Test creating ApiError with description only"""
        error = ApiError("Bad Request")
        assert error.description == "Bad Request"
        assert error.status_code is None
        assert "API Error: Bad Request" in str(error)
        assert isinstance(error, YMBotError)

    def test_create_api_error_with_status_code(self):
        """Test creating ApiError with status code"""
        error = ApiError("Unauthorized", status_code=401)
        assert error.description == "Unauthorized"
        assert error.status_code == 401
        assert "API Error: Unauthorized" in str(error)
        assert "status: 401" in str(error)

    def test_api_error_with_http_400(self):
        """Test ApiError with 400 status"""
        error = ApiError("Bad Request", status_code=400)
        assert error.status_code == 400

    def test_api_error_with_http_404(self):
        """Test ApiError with 404 status"""
        error = ApiError("Not Found", status_code=404)
        assert error.status_code == 404

    def test_api_error_with_http_500(self):
        """Test ApiError with 500 status"""
        error = ApiError("Internal Server Error", status_code=500)
        assert error.status_code == 500

    def test_raise_api_error(self):
        """Test raising ApiError"""
        with pytest.raises(ApiError) as exc_info:
            raise ApiError("Invalid token", status_code=401)
        assert exc_info.value.description == "Invalid token"
        assert exc_info.value.status_code == 401


class TestValidationError:
    """Tests for ValidationError class"""

    def test_create_validation_error_with_message_only(self):
        """Test creating ValidationError with message only"""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert error.field is None
        assert isinstance(error, YMBotError)

    def test_create_validation_error_with_field(self):
        """Test creating ValidationError with field"""
        error = ValidationError("Invalid input", field="email")
        assert str(error) == "Invalid input"
        assert error.field == "email"

    def test_validation_error_field_default(self):
        """Test that default field is None"""
        error = ValidationError("Test error")
        assert error.field is None

    def test_validation_error_various_fields(self):
        """Test ValidationError with different fields"""
        fields = ["token", "polling_limit", "max_retries", "concurrency"]
        for field in fields:
            error = ValidationError(f"Invalid {field}", field=field)
            assert error.field == field

    def test_raise_validation_error(self):
        """Test raising ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid token", field="token")
        assert str(exc_info.value) == "Invalid token"
        assert exc_info.value.field == "token"


class TestOffsetError:
    """Tests for OffsetError class"""

    def test_create_offset_error(self):
        """Test creating OffsetError"""
        error = OffsetError("Invalid offset")
        assert str(error) == "Invalid offset"
        assert isinstance(error, YMBotError)

    def test_raise_offset_error(self):
        """Test raising OffsetError"""
        with pytest.raises(OffsetError) as exc_info:
            raise OffsetError("Offset out of range")
        assert str(exc_info.value) == "Offset out of range"


class TestAssertOk:
    """Tests for assert_ok function"""

    def test_assert_ok_with_ok_true(self):
        """Test assert_ok with ok=True response"""
        response = {"ok": True, "result": {"data": "test"}}
        assert_ok(response)  # Should not raise

    def test_assert_ok_with_ok_false(self):
        """Test assert_ok with ok=False raises ApiError"""
        response = {"ok": False, "description": "Invalid token"}
        with pytest.raises(ApiError) as exc_info:
            assert_ok(response)
        assert exc_info.value.description == "Invalid token"

    def test_assert_ok_with_missing_description(self):
        """Test assert_ok with missing description"""
        response = {"ok": False}
        with pytest.raises(ApiError) as exc_info:
            assert_ok(response)
        assert exc_info.value.description == "Unknown error"

    def test_assert_ok_with_description_present(self):
        """Test assert_ok uses description from response"""
        response = {"ok": False, "description": "Bad request"}
        with pytest.raises(ApiError) as exc_info:
            assert_ok(response)
        assert exc_info.value.description == "Bad request"

    def test_assert_ok_with_missing_ok(self):
        """Test assert_ok with missing ok field"""
        response = {"result": {"data": "test"}}
        with pytest.raises(ApiError) as exc_info:
            assert_ok(response)
        assert exc_info.value.description == "Unknown error"

    def test_assert_ok_with_empty_response(self):
        """Test assert_ok with empty response"""
        response = {}
        with pytest.raises(ApiError) as exc_info:
            assert_ok(response)
        assert exc_info.value.description == "Unknown error"

    def test_assert_ok_with_additional_fields(self):
        """Test assert_ok doesn't fail with additional fields"""
        response = {
            "ok": True,
            "result": {"data": "test"},
            "extra": "field",
            "more": 123,
        }
        assert_ok(response)  # Should not raise

    def test_assert_ok_status_code_none(self):
        """Test assert_ok sets status_code to None"""
        response = {"ok": False, "description": "Error"}
        with pytest.raises(ApiError) as exc_info:
            assert_ok(response)
        assert exc_info.value.status_code is None


class TestErrorHierarchy:
    """Tests for error class hierarchy"""

    def test_all_errors_inherit_from_ymbot_error(self):
        """Test that all error classes inherit from YMBotError"""
        errors = [
            TransportError("test"),
            ApiError("test"),
            ValidationError("test"),
            OffsetError("test"),
        ]
        for error in errors:
            assert isinstance(error, YMBotError)

    def test_errors_catchable_by_base_class(self):
        """Test that all errors can be caught by YMBotError"""
        with pytest.raises(YMBotError):
            raise TransportError("test")
        with pytest.raises(YMBotError):
            raise ApiError("test")
        with pytest.raises(YMBotError):
            raise ValidationError("test")
        with pytest.raises(YMBotError):
            raise OffsetError("test")

    def test_specific_errors_catchable_by_specific_class(self):
        """Test that specific errors can be caught by their specific class"""
        with pytest.raises(TransportError):
            raise TransportError("test")
        with pytest.raises(ApiError):
            raise ApiError("test")
        with pytest.raises(ValidationError):
            raise ValidationError("test")
        with pytest.raises(OffsetError):
            raise OffsetError("test")