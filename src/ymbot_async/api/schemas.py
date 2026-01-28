"""
Pydantic schemas for API request/response validation
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class User(BaseModel):
    """User information"""

    id: str = Field(..., description="User ID (GUID)")
    login: str = Field(default="", description="User login")
    display_name: str = Field(default="", description="User display name")
    robot: bool = Field(default=False, description="Whether user is a bot")


class Chat(BaseModel):
    """Chat information"""

    type: Literal["private", "group", "channel"] = Field(
        ..., description="Chat type"
    )
    id: str | None = Field(default=None, description="Chat ID (absent for private chats)")


class Sender(BaseModel):
    """Sender information (for messages)"""

    login: str | None = Field(default=None, description="User login (for chats)")
    id: str | None = Field(default=None, description="Channel ID (for channels)")
    display_name: str | None = Field(default=None, description="Display name")
    robot: bool | None = Field(default=False, description="Whether sender is a bot")


class File(BaseModel):
    """File information"""

    id: str = Field(..., description="File ID for download via API")
    name: str = Field(..., description="File name")
    size: int | None = Field(default=None, description="File size in bytes")


class Image(BaseModel):
    """Image information"""

    file_id: str = Field(..., description="File ID for download via API")
    width: int = Field(..., description="Image width")
    height: int = Field(..., description="Image height")
    size: int | None = Field(default=None, description="File size in bytes (original only)")
    name: str | None = Field(default=None, description="File name (original only)")


class Update(BaseModel):
    """Update object from webhook or long polling"""

    model_config = ConfigDict(extra="allow")

    update_id: int = Field(..., description="Update ID")
    message_id: int = Field(..., description="Message ID in chat")
    timestamp: int = Field(..., description="Message timestamp (UNIX timestamp)")
    chat: Chat = Field(..., description="Chat where message was sent")
    from_user: Sender = Field(..., alias="from", description="Sender")
    text: str | None = Field(default=None, description="Message text")
    file: File | None = Field(default=None, description="Attached file")
    images: list[list[Image]] | None = Field(default=None, description="Attached images (gallery)")
    sticker: dict | None = Field(default=None, description="Sticker")
    forwarded_messages: list | None = Field(default=None, description="Forwarded messages")


class InlineButton(BaseModel):
    """Inline keyboard button"""

    text: str = Field(..., description="Button text")
    url: str | None = Field(default=None, description="Button URL")
    callback_data: Any | None = Field(default=None, description="Callback data")

    @model_validator(mode="after")
    def validate_has_action(self) -> "InlineButton":
        """Ensure button has at least one action"""
        if self.url is None and self.callback_data is None:
            raise ValueError("Button must have either url or callback_data")
        return self


class InlineKeyboardMarkup(BaseModel):
    """Inline keyboard markup"""

    inline_keyboard: list[list[InlineButton]] = Field(
        default_factory=list,
        description="Keyboard rows with buttons",
    )


class MessageResponse(BaseModel):
    """Response from sendText API method"""

    model_config = ConfigDict(extra="allow")

    ok: bool = Field(..., description="Request success status")
    message_id: int = Field(..., description="Sent message ID")


class GetUpdatesResponse(BaseModel):
    """Response from getUpdates API method"""

    model_config = ConfigDict(extra="allow")

    ok: bool = Field(..., description="Request success status")
    updates: list[Update] = Field(default_factory=list, description="List of updates")


class SendTextRequest(BaseModel):
    """Request for sendText API method"""

    chat_id: str | None = Field(default=None, description="Chat ID")
    login: str | None = Field(default=None, description="User login")
    text: str = Field(..., description="Message text")
    payload_id: str | None = Field(default=None, description="Request ID")
    reply_message_id: int | None = Field(default=None, description="Reply to message ID")
    disable_notification: bool | None = Field(default=None, description="Disable notifications")
    important: bool | None = Field(default=None, description="Mark as important")
    disable_web_page_preview: bool | None = Field(default=None, description="Disable link preview")
    thread_id: int | None = Field(default=None, description="Thread ID")
    inline_keyboard: list[list[InlineButton]] | None = Field(
        default=None, description="Inline keyboard"
    )

    @model_validator(mode="after")
    def validate_chat_or_login(self) -> "SendTextRequest":
        """Ensure at least one of chat_id or login is provided"""
        if self.chat_id is None and self.login is None:
            raise ValueError("Must provide either chat_id or login")
        return self