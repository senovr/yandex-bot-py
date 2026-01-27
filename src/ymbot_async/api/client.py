"""
API client for Yandex Messenger Bot Async Client
"""

from typing import Any

from ymbot_async.api.schemas import (
    GetUpdatesResponse,
    InlineKeyboardMarkup,
    MessageResponse,
    SendMessageRequest,
)
from ymbot_async.transport.httpx_transport import HttpxTransport
from ymbot_async.logging import get_logger, LoggerProtocol

logger: LoggerProtocol = get_logger(__name__)


class ApiClient:
    """
    High-level API client for Yandex Messenger Bot.
    
    Provides typed methods for API calls using the transport layer.
    """

    def __init__(self, transport: HttpxTransport):
        """
        Initialize API client.
        
        Args:
            transport: HTTP transport instance
        """
        self.transport = transport

    async def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: float = 1.0,
    ) -> GetUpdatesResponse:
        """
        Get updates via long polling.
        
        Args:
            offset: Offset to start from (exclusive)
            limit: Maximum number of updates (1-1000)
            timeout: Timeout in seconds to wait for new updates
            
        Returns:
            Response with list of updates
        """
        params: dict[str, Any] = {"limit": limit, "timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        logger.debug(
            "Fetching updates",
            offset=offset,
            limit=limit,
            timeout=timeout,
        )

        response = await self.transport.request(
            method="GET",
            path="/messages/getUpdates",
            params=params,
        )

        return GetUpdatesResponse.model_validate(response)

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> MessageResponse:
        """
        Send a message to a chat.
        
        Args:
            chat_id: Chat ID to send message to
            text: Message text
            parse_mode: Parse mode (Markdown or HTML)
            reply_markup: Inline keyboard markup
            
        Returns:
            Response with sent message
        """
        request = SendMessageRequest(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )

        logger.info(
            "Sending message",
            chat_id=chat_id,
            text_length=len(text),
            has_keyboard=reply_markup is not None,
        )

        response = await self.transport.request(
            method="POST",
            path="/messages/sendMessage",
            json=request.model_dump(exclude_none=True, by_alias=True),
        )

        return MessageResponse.model_validate(response)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict[str, Any]:
        """
        Answer a callback query.
        
        Args:
            callback_query_id: Callback query ID
            text: Notification text
            show_alert: Whether to show as alert
            
        Returns:
            API response
        """
        body: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            body["text"] = text
        body["show_alert"] = show_alert

        logger.debug(
            "Answering callback query",
            callback_query_id=callback_query_id,
            has_text=text is not None,
        )

        return await self.transport.request(
            method="POST",
            path="/messages/answerCallbackQuery",
            json=body,
        )

    async def edit_message_text(
        self,
        chat_id: str,
        message_id: str,
        text: str,
        parse_mode: str | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> MessageResponse:
        """
        Edit a message's text.
        
        Args:
            chat_id: Chat ID
            message_id: Message ID to edit
            text: New message text
            parse_mode: Parse mode (Markdown or HTML)
            reply_markup: New inline keyboard markup
            
        Returns:
            Response with edited message
        """
        body: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            body["parse_mode"] = parse_mode
        if reply_markup:
            body["reply_markup"] = reply_markup.model_dump(
                exclude_none=True, by_alias=True
            )

        logger.info(
            "Editing message",
            chat_id=chat_id,
            message_id=message_id,
            text_length=len(text),
        )

        response = await self.transport.request(
            method="POST",
            path="/messages/editMessageText",
            json=body,
        )

        return MessageResponse.model_validate(response)

    async def delete_message(
        self,
        chat_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """
        Delete a message.
        
        Args:
            chat_id: Chat ID
            message_id: Message ID to delete
            
        Returns:
            API response
        """
        logger.info(
            "Deleting message",
            chat_id=chat_id,
            message_id=message_id,
        )

        return await self.transport.request(
            method="POST",
            path="/messages/deleteMessage",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
            },
        )