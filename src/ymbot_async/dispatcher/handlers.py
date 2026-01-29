"""
Handler base classes and implementations
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from ymbot_async.api.schemas import Update


class Handler(ABC):
    """Base handler class"""

    @abstractmethod
    def check(self, update: Update) -> bool:
        """
        Check if handler can handle this update.

        Args:
            update: Update to check

        Returns:
            True if handler can handle update
        """
        pass

    @abstractmethod
    async def handle(self, update: Update) -> Any:
        """
        Handle the update.

        Args:
            update: Update to handle

        Returns:
            Handler result (optional)
        """
        pass


class MessageHandler(Handler):
    """Handler for message updates"""

    def __init__(
        self,
        callback: Callable[[Update], Awaitable[Any]],
        filters: Any = None,
    ):
        """
        Initialize message handler.

        Args:
            callback: Async function to call when handler matches
            filters: Filter(s) to apply
        """
        self.callback = callback
        self.filters = filters

    async def handle(self, update: Update) -> Any:
        """Handle update by calling callback"""
        return await self.callback(update)

    def check(self, update: Update) -> bool:
        """Check if update matches handler filters"""
        # MessageHandler matches if update has text content
        if update.text is None:
            return False

        if self.filters is None:
            return True

        # Support single filter or list of filters
        filters_list = self.filters if isinstance(self.filters, list) else [self.filters]

        return all(filter_obj.check(update) for filter_obj in filters_list)


class CallbackQueryHandler(Handler):
    """Handler for callback query updates"""

    def __init__(
        self,
        callback: Callable[[Update], Awaitable[Any]],
        filters: Any = None,
    ):
        """
        Initialize callback query handler.

        Args:
            callback: Async function to call when handler matches
            filters: Filter(s) to apply
        """
        self.callback = callback
        self.filters = filters

    async def handle(self, update: Update) -> Any:
        """Handle update by calling callback"""
        return await self.callback(update)

    def check(self, update: Update) -> bool:
        """Check if update matches handler filters"""
        # Check if update has callback data (text field)
        if not update.text:
            return False

        if self.filters is None:
            return True

        # Support single filter or list of filters
        filters_list = self.filters if isinstance(self.filters, list) else [self.filters]

        return all(filter_obj.check(update) for filter_obj in filters_list)
