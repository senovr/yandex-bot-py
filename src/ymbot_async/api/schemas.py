"""
Pydantic schemas for API request/response validation
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class User(BaseModel):
    """User information"""

    id: str = Field(..., description="User ID")
    name: str = Field(default="", description="User display name")


class Chat(BaseModel):
    """Chat information"""

    id: str = Field(..., description="Chat ID")
    type: Literal["private", "group", "channel"] = Field(
        ..., description="Chat type"
    )
    name: str = Field(default="", description="Chat display name")


class Message(BaseModel):
    """Message content"""

    model_config = ConfigDict(populate_by_name=True)  # Allow using both field name and alias

    id: str = Field(..., description="Message ID")
    text: str = Field(..., description="Message text")
    timestamp: str = Field(..., description="Message timestamp (ISO 8601)")
    from_user: User | None = Field(None, alias="from", description="Sender")
    chat: Chat = Field(..., description="Chat where message was sent")


class Update(BaseModel):
    """Update object from webhook or long polling"""

    update_id: int = Field(..., description="Update ID")
    message: Message | None = Field(None, description="New message")
    callback_query: dict | None = Field(None, description="Callback query")


class InlineButton(BaseModel):
    """Inline keyboard button"""

    text: str = Field(..., description="Button text")
    url: str | None = Field(None, description="Button URL")
    callback_data: str | None = Field(None, description="Callback data")

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
    """Response from sendMessage API method"""

    model_config = ConfigDict(extra="allow")  # Allow extra fields in API responses

    ok: bool = Field(..., description="Request success status")
    message: Message = Field(..., description="Sent message")


class GetUpdatesResponse(BaseModel):
    """Response from getUpdates API method"""

    model_config = ConfigDict(extra="allow")

    ok: bool = Field(..., description="Request success status")
    updates: list[Update] = Field(default_factory=list, description="List of updates")


class SendMessageRequest(BaseModel):
    """Request for sendMessage API method"""

    chat_id: str = Field(..., description="Chat ID")
    text: str = Field(..., description="Message text")
    parse_mode: Literal["Markdown", "HTML"] | None = Field(
        None, description="Text parse mode"
    )
    reply_markup: InlineKeyboardMarkup | None = Field(
        None, description="Inline keyboard markup"
    )