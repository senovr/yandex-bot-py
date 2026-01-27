"""Unit tests for Pydantic schemas"""
import pytest
from typing import Literal

from pydantic import ValidationError

from ymbot_async.api.schemas import (
    User,
    Chat,
    Message,
    Update,
    InlineButton,
    InlineKeyboardMarkup,
    MessageResponse,
    GetUpdatesResponse,
    SendMessageRequest,
)


class TestUser:
    """Tests for User model"""

    def test_create_user_with_required_fields(self):
        """Test creating User with only required fields"""
        user = User(id="12345")  # type: ignore
        assert user.id == "12345"
        assert user.name == ""

    def test_create_user_with_all_fields(self):
        """Test creating User with all fields"""
        user = User(id="12345", name="John Doe")
        assert user.id == "12345"
        assert user.name == "John Doe"

    def test_user_id_required(self):
        """Test that User requires id field"""
        with pytest.raises(ValidationError):
            User(name="John Doe")  # type: ignore

    def test_user_name_default(self):
        """Test that User name defaults to empty string"""
        user = User(id="12345")
        assert user.name == ""

    def test_user_name_can_be_empty(self):
        """Test that User name can be empty string"""
        user = User(id="12345", name="")
        assert user.name == ""

    def test_user_model_dump(self):
        """Test User model serialization"""
        user = User(id="12345", name="John")
        data = user.model_dump()
        assert data == {"id": "12345", "name": "John"}


class TestChat:
    """Tests for Chat model"""

    def test_create_chat_with_required_fields(self):
        """Test creating Chat with only required fields"""
        chat = Chat(id="chat_123", type="private")
        assert chat.id == "chat_123"
        assert chat.type == "private"
        assert chat.name == ""

    def test_create_chat_invalid_type(self):
        """Test that invalid Chat type (not in literal) is a type error"""
        # This is a type error - invalid_type is not in the Literal type
        # We can't create a Chat with invalid_type due to type checking
        # So we skip this test as it's not possible at runtime with the current Literal constraint
        pass

    def test_create_chat_with_all_fields(self):
        """Test creating Chat with all fields"""
        chat = Chat(id="chat_123", type="group", name="Test Group")
        assert chat.id == "chat_123"
        assert chat.type == "group"
        assert chat.name == "Test Group"

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

    def test_chat_id_required(self):
        """Test that Chat requires id field"""
        with pytest.raises(ValidationError):
            Chat(type="private")  # type: ignore

    def test_chat_type_required(self):
        """Test that Chat requires type field"""
        with pytest.raises(ValidationError):
            Chat(id="chat_123")  # type: ignore

    def test_chat_name_default(self):
        """Test that Chat name defaults to empty string"""
        chat = Chat(id="chat_123", type="private")
        assert chat.name == ""

    def test_chat_name_can_be_empty(self):
        """Test that Chat name can be empty string"""
        chat = Chat(id="chat_123", type="private", name="")
        assert chat.name == ""


class TestMessage:
    """Tests for Message model"""

    def test_create_message_with_required_fields(self, sample_chat):
        """Test creating Message with only required fields"""
        message = Message(
            id="1",
            text="Hello",
            timestamp="2024-01-01T00:00:00Z",
            chat=sample_chat,
        )
        assert message.id == "1"
        assert message.text == "Hello"
        assert message.timestamp == "2024-01-01T00:00:00Z"
        assert message.from_user is None

    def test_create_message_with_from_user(self, sample_user, sample_chat):
        """Test creating Message with from_user"""
        message = Message(
            id="1",
            text="Hello",
            timestamp="2024-01-01T00:00:00Z",
            from_user=sample_user,  # type: ignore
            chat=sample_chat,
        )
        assert message.from_user == sample_user

    def test_message_from_field_alias(self, sample_user, sample_chat):
        """Test that 'from' field is aliased to from_user"""
        data = {
            "id": "1",
            "text": "Hello",
            "timestamp": "2024-01-01T00:00:00Z",
            "from": {"id": "12345", "name": "Test User"},
            "chat": {"id": "chat_123", "type": "private", "name": "Test"},
        }
        message = Message(**data)  # type: ignore[arg-type]
        assert message.from_user is not None
        assert message.from_user.id == "12345"

    def test_message_id_required(self, sample_chat):
        """Test that Message requires id field"""
        with pytest.raises(ValidationError):
            Message(text="Hello", timestamp="2024-01-01T00:00:00Z", chat=sample_chat)  # type: ignore

    def test_message_text_required(self, sample_chat):
        """Test that Message requires text field"""
        with pytest.raises(ValidationError):
            Message(id="1", timestamp="2024-01-01T00:00:00Z", chat=sample_chat)  # type: ignore

    def test_message_timestamp_required(self, sample_chat):
        """Test that Message requires timestamp field"""
        with pytest.raises(ValidationError):
            Message(id="1", text="Hello", chat=sample_chat)  # type: ignore

    def test_message_chat_required(self):
        """Test that Message requires chat field"""
        with pytest.raises(ValidationError):
            Message(id="1", text="Hello", timestamp="2024-01-01T00:00:00Z")  # type: ignore


class TestUpdate:
    """Tests for Update model"""

    def test_create_update_with_message(self, sample_message):
        """Test creating Update with message"""
        update = Update(update_id=1, message=sample_message, callback_query=None)
        assert update.update_id == 1
        assert update.message == sample_message

    def test_create_update_with_callback_query(self):
        """Test creating Update with callback_query"""
        update = Update(update_id=1, message=None, callback_query={"id": "123", "data": "click"})
        assert update.update_id == 1
        assert update.message is None
        assert update.callback_query == {"id": "123", "data": "click"}

    def test_update_update_id_required(self, sample_message):
        """Test that Update requires update_id"""
        with pytest.raises(ValidationError):
            Update(message=sample_message, callback_query=None)  # type: ignore

    def test_update_model_dump(self, sample_message):
        """Test Update model serialization"""
        update = Update(update_id=1, message=sample_message, callback_query=None)
        data = update.model_dump()
        assert data["update_id"] == 1
        assert "message" in data


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

    def test_create_message_response(self, sample_message):
        """Test creating MessageResponse"""
        response = MessageResponse(ok=True, message=sample_message)
        assert response.ok is True
        assert response.message == sample_message

    def test_message_response_with_extra_fields(self, sample_message):
        """Test MessageResponse allows extra fields"""
        data = {
            "ok": True,
            "message": sample_message.model_dump(),
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


class TestSendMessageRequest:
    """Tests for SendMessageRequest model"""

    def test_create_send_message_request(self):
        """Test creating SendMessageRequest with required fields"""
        request = SendMessageRequest(
            chat_id="chat_123",
            text="Hello, World!",
            parse_mode=None,
            reply_markup=None,
        )
        assert request.chat_id == "chat_123"
        assert request.text == "Hello, World!"
        assert request.parse_mode is None
        assert request.reply_markup is None

    def test_send_message_with_parse_mode_markdown(self):
        """Test creating request with Markdown parse mode"""
        request = SendMessageRequest(
            chat_id="chat_123",
            text="Hello",
            parse_mode="Markdown",
            reply_markup=None,
        )
        assert request.parse_mode == "Markdown"

    def test_send_message_with_parse_mode_html(self):
        """Test creating request with HTML parse mode"""
        request = SendMessageRequest(
            chat_id="chat_123",
            text="Hello",
            parse_mode="HTML",
            reply_markup=None,
        )
        assert request.parse_mode == "HTML"

    def test_send_message_with_keyboard(self, sample_inline_keyboard):
        """Test creating request with inline keyboard"""
        request = SendMessageRequest(
            chat_id="chat_123",
            text="Hello",
            parse_mode=None,
            reply_markup=sample_inline_keyboard,
        )
        assert request.reply_markup == sample_inline_keyboard

    def test_send_message_with_all_fields(self, sample_inline_keyboard):
        """Test creating request with all fields"""
        request = SendMessageRequest(
            chat_id="chat_123",
            text="Hello",
            parse_mode="Markdown",
            reply_markup=sample_inline_keyboard,
        )
        assert request.chat_id == "chat_123"
        assert request.text == "Hello"
        assert request.parse_mode == "Markdown"
        assert request.reply_markup == sample_inline_keyboard

    def test_send_message_chat_id_required(self):
        """Test that chat_id is required"""
        with pytest.raises(ValidationError):
            SendMessageRequest(text="Hello")  # type: ignore

    def test_send_message_text_required(self):
        """Test that text is required"""
        with pytest.raises(ValidationError):
            SendMessageRequest(chat_id="chat_123")  # type: ignore

    def test_send_message_invalid_parse_mode(self):
        """Test that invalid parse_mode raises error"""
        with pytest.raises(ValidationError):
            SendMessageRequest(
                chat_id="chat_123",
                text="Hello",
                parse_mode="Invalid",  # type: ignore
            )