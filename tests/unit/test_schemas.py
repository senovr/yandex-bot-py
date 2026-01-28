"""Unit tests for Pydantic schemas"""
import pytest
from typing import Literal

from pydantic import ValidationError

from ymbot_async.api.schemas import (
    Chat,
    Sender,
    Update,
    InlineButton,
    InlineKeyboardMarkup,
    MessageResponse,
    GetUpdatesResponse,
    SendTextRequest,
)


class TestChat:
    """Tests for Chat model"""

    def test_create_chat_with_type_only(self):
        """Test creating Chat with only type field (id is optional)"""
        chat = Chat(type="private")
        assert chat.type == "private"
        assert chat.id is None

    def test_create_chat_with_id_and_type(self):
        """Test creating Chat with id and type"""
        chat = Chat(id="chat_123", type="group")
        assert chat.id == "chat_123"
        assert chat.type == "group"

    def test_chat_type_private(self):
        """Test Chat type can be private"""
        chat = Chat(id="chat_123", type="private")
        assert chat.type == "private"

    def test_chat_type_group(self):
        """Test Chat type can be group"""
        chat = Chat(id="chat_123", type="group")
        assert chat.type == "group"

    def test_chat_type_channel(self):
        """Test Chat type can be channel"""
        chat = Chat(id="chat_123", type="channel")
        assert chat.type == "channel"

    def test_chat_type_invalid(self):
        """Test that invalid Chat type raises error"""
        with pytest.raises(ValidationError):
            Chat(id="chat_123", type="invalid_type")  # type: ignore

    def test_chat_type_required(self):
        """Test that Chat requires type field"""
        with pytest.raises(ValidationError):
            Chat(id="chat_123")  # type: ignore


class TestUpdate:
    """Tests for Update model"""

    def test_create_update_with_text_message(self):
        """Test creating Update with text message"""
        update = Update(
            update_id=1,
            message_id=123,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="test", display_name="Test")},
            text="Hello",
        )
        assert update.update_id == 1
        assert update.message_id == 123
        assert update.text == "Hello"

    def test_update_update_id_required(self):
        """Test that Update requires update_id"""
        with pytest.raises(ValidationError):
            Update(
                message_id=123,
                timestamp=1704067200,
                chat=Chat(type="private"),
                **{"from": Sender(login="test", display_name="Test")},
                text="Hello",
            )  # type: ignore

    def test_update_model_dump(self):
        """Test Update model serialization"""
        update = Update(
            update_id=1,
            message_id=123,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="test", display_name="Test")},
            text="Hello",
        )
        data = update.model_dump()
        assert data["update_id"] == 1
        assert data["message_id"] == 123


class TestInlineButton:
    """Tests for InlineButton model"""

    def test_create_button_with_url(self):
        """Test creating InlineButton with url"""
        button = InlineButton(text="Click Me", url="https://example.com", callback_data=None)
        assert button.text == "Click Me"
        assert button.url == "https://example.com"
        assert button.callback_data is None

    def test_create_button_with_callback_data(self):
        """Test creating InlineButton with callback_data"""
        button = InlineButton(text="Click Me", callback_data="btn_click", url=None)
        assert button.text == "Click Me"
        assert button.callback_data == "btn_click"
        assert button.url is None

    def test_button_requires_action(self):
        """Test that button requires either url or callback_data"""
        with pytest.raises(ValidationError):
            InlineButton(text="Click Me")  # type: ignore[call-arg]

    def test_button_text_required(self):
        """Test that button requires text"""
        with pytest.raises(ValidationError):
            InlineButton(url="https://example.com")  # type: ignore[call-arg]

    def test_button_url_and_callback_mutually_exclusive(self):
        """Test that button can have url or callback_data but both work"""
        button = InlineButton(text="Click Me", url="url", callback_data="data")
        # Both should be set - validator allows both
        assert button.url == "url"
        assert button.callback_data == "data"

    def test_button_url_only(self):
        """Test that button can have only url"""
        button = InlineButton(text="Click Me", url="https://example.com", callback_data=None)
        assert button.url == "https://example.com"
        assert button.callback_data is None

    def test_button_callback_data_only(self):
        """Test that button can have only callback_data"""
        button = InlineButton(text="Click Me", callback_data="btn_click", url=None)
        assert button.callback_data == "btn_click"
        assert button.url is None

    def test_button_url_can_be_none(self):
        """Test that button url can be None if callback_data is set"""
        button = InlineButton(text="Click Me", callback_data="data")
        assert button.url is None

    def test_button_callback_data_can_be_none(self):
        """Test that button callback_data can be None if url is set"""
        button = InlineButton(text="Click Me", url="https://example.com")
        assert button.callback_data is None


class TestInlineKeyboardMarkup:
    """Tests for InlineKeyboardMarkup model"""

    def test_create_empty_keyboard(self):
        """Test creating empty InlineKeyboardMarkup"""
        keyboard = InlineKeyboardMarkup()
        assert keyboard.inline_keyboard == []

    def test_create_keyboard_with_buttons(self, sample_inline_button):
        """Test creating keyboard with buttons"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[sample_inline_button]])
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 1
        assert keyboard.inline_keyboard[0][0] == sample_inline_button

    def test_create_keyboard_with_multiple_rows(self, sample_inline_button):
        """Test creating keyboard with multiple rows"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [sample_inline_button, sample_inline_button],
                [sample_inline_button],
            ]
        )
        assert len(keyboard.inline_keyboard) == 2
        assert len(keyboard.inline_keyboard[0]) == 2
        assert len(keyboard.inline_keyboard[1]) == 1

    def test_keyboard_default_factory(self):
        """Test that inline_keyboard has default factory"""
        keyboard = InlineKeyboardMarkup()
        assert keyboard.inline_keyboard == []


class TestMessageResponse:
    """Tests for MessageResponse model"""

    def test_create_message_response(self):
        """Test creating MessageResponse"""
        response = MessageResponse(ok=True, message_id=123)
        assert response.ok is True
        assert response.message_id == 123

    def test_message_response_with_extra_fields(self):
        """Test MessageResponse allows extra fields"""
        data = {
            "ok": True,
            "message_id": 123,
            "extra_field": "value",
        }
        response = MessageResponse(**data)
        assert response.ok is True


class TestGetUpdatesResponse:
    """Tests for GetUpdatesResponse model"""

    def test_create_empty_updates_response(self):
        """Test creating GetUpdatesResponse with no updates"""
        response = GetUpdatesResponse(ok=True, updates=[])
        assert response.ok is True
        assert response.updates == []

    def test_create_updates_response(self, sample_update):
        """Test creating GetUpdatesResponse with updates"""
        response = GetUpdatesResponse(ok=True, updates=[sample_update])
        assert response.ok is True
        assert len(response.updates) == 1
        assert response.updates[0] == sample_update

    def test_updates_default_factory(self):
        """Test that updates has default factory"""
        response = GetUpdatesResponse(ok=True)
        assert response.updates == []

    def test_get_updates_response_with_extra_fields(self):
        """Test GetUpdatesResponse allows extra fields"""
        data = {"ok": True, "updates": [], "extra": "field"}
        response = GetUpdatesResponse(**data)
        assert response.ok is True


class TestSendTextRequest:
    """Tests for SendTextRequest model"""

    def test_create_send_text_request(self):
        """Test creating SendTextRequest with required fields"""
        request = SendTextRequest(
            chat_id="chat_123",
            text="Hello, World!",
            inline_keyboard=None,
        )
        assert request.chat_id == "chat_123"
        assert request.text == "Hello, World!"
        assert request.inline_keyboard is None

    def test_send_text_with_keyboard(self, sample_inline_keyboard_buttons):
        """Test creating request with inline keyboard"""
        request = SendTextRequest(
            chat_id="chat_123",
            text="Hello",
            inline_keyboard=sample_inline_keyboard_buttons,
        )
        assert request.inline_keyboard == sample_inline_keyboard_buttons

    def test_send_text_with_all_fields(self, sample_inline_keyboard_buttons):
        """Test creating request with all fields"""
        request = SendTextRequest(
            chat_id="chat_123",
            text="Hello",
            inline_keyboard=sample_inline_keyboard_buttons,
        )
        assert request.chat_id == "chat_123"
        assert request.text == "Hello"
        assert request.inline_keyboard == sample_inline_keyboard_buttons

    def test_send_text_chat_id_required(self):
        """Test that chat_id is required"""
        with pytest.raises(ValidationError):
            SendTextRequest(text="Hello")  # type: ignore

    def test_send_text_text_required(self):
        """Test that text is required"""
        with pytest.raises(ValidationError):
            SendTextRequest(chat_id="chat_123")  # type: ignore
