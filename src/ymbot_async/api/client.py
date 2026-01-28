"""
API client for Yandex Messenger Bot Async Client
"""

from typing import Any

from ymbot_async.api.schemas import (
    GetUpdatesResponse,
    InlineButton,
    MessageResponse,
    SendTextRequest,
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
            path="/messages/getUpdates/",
            params=params,
        )

        return GetUpdatesResponse.model_validate(response)

    async def send_message(
        self,
        chat_id: str | None = None,
        login: str | None = None,
        text: str = "",
        payload_id: str | None = None,
        reply_message_id: int | None = None,
        disable_notification: bool | None = None,
        important: bool | None = None,
        disable_web_page_preview: bool | None = None,
        thread_id: int | None = None,
        inline_keyboard: list[list[InlineButton]] | None = None,
    ) -> MessageResponse:
        """
        Send a text message to a chat.
        
        Args:
            chat_id: Chat ID to send message to (for group/channel)
            login: User login to send message to (for private chat)
            text: Message text
            payload_id: Request ID
            reply_message_id: Reply to message ID
            disable_notification: Disable notifications
            important: Mark as important
            disable_web_page_preview: Disable link preview
            thread_id: Thread ID
            inline_keyboard: Inline keyboard markup
            
        Returns:
            Response with sent message
        """
        request = SendTextRequest(
            chat_id=chat_id,
            login=login,
            text=text,
            payload_id=payload_id,
            reply_message_id=reply_message_id,
            disable_notification=disable_notification,
            important=important,
            disable_web_page_preview=disable_web_page_preview,
            thread_id=thread_id,
            inline_keyboard=inline_keyboard,
        )

        logger.info(
            "Sending message",
            chat_id=chat_id,
            login=login,
            text_length=len(text),
            has_keyboard=inline_keyboard is not None,
        )

        response = await self.transport.request(
            method="POST",
            path="/messages/sendText/",
            json=request.model_dump(exclude_none=True, by_alias=True),
        )

        return MessageResponse.model_validate(response)

    async def delete_message(
        self,
        chat_id: str | None = None,
        login: str | None = None,
        message_id: int = 0,
        thread_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Delete a message.
        
        Args:
            chat_id: Chat ID (for group/channel)
            login: User login (for private chat)
            message_id: Message ID to delete
            thread_id: Thread ID
            
        Returns:
            API response
        """
        body: dict[str, Any] = {"message_id": message_id}
        if chat_id:
            body["chat_id"] = chat_id
        if login:
            body["login"] = login
        if thread_id:
            body["thread_id"] = thread_id

        logger.info(
            "Deleting message",
            chat_id=chat_id,
            login=login,
            message_id=message_id,
        )

        return await self.transport.request(
            method="POST",
            path="/messages/delete/",
            json=body,
        )