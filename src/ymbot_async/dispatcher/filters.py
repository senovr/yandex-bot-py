"""
Filters for update matching
"""

import re
from abc import ABC, abstractmethod

from ymbot_async.api.schemas import Update


class Filter(ABC):
    """Base filter class"""

    @abstractmethod
    def check(self, update: Update) -> bool:
        """
        Check if update matches filter.

        Args:
            update: Update to check

        Returns:
            True if update matches filter
        """
        ...

    def __and__(self, other: "Filter") -> "AndFilter":
        """Combine filters with AND logic"""
        return AndFilter(self, other)

    def __or__(self, other: "Filter") -> "OrFilter":
        """Combine filters with OR logic"""
        return OrFilter(self, other)

    def __invert__(self) -> "NotFilter":
        """Negate filter"""
        return NotFilter(self)


class AndFilter(Filter):
    """AND logic for combining filters"""

    def __init__(self, *filters: Filter):
        self.filters = filters

    def check(self, update: Update) -> bool:
        return all(f.check(update) for f in self.filters)


class OrFilter(Filter):
    """OR logic for combining filters"""

    def __init__(self, *filters: Filter):
        self.filters = filters

    def check(self, update: Update) -> bool:
        return any(f.check(update) for f in self.filters)


class NotFilter(Filter):
    """NOT logic for negating filter"""

    def __init__(self, filter_obj: Filter):
        self.filter = filter_obj

    def check(self, update: Update) -> bool:
        return not self.filter.check(update)


class TextFilter(Filter):
    """Filter by message text"""

    def __init__(self, text: str | re.Pattern[str] | None = None):
        """
        Initialize text filter.

        Args:
            text: Text to match (string or regex pattern)
        """
        self.text = text

    def check(self, update: Update) -> bool:
        message_text = update.text

        if self.text is None:
            return bool(message_text)

        if isinstance(self.text, re.Pattern):
            return bool(self.text.search(message_text)) if message_text else False

        return message_text == self.text


class CommandFilter(Filter):
    """Filter by bot command (e.g., /start, /help)"""

    def __init__(
        self,
        command: str | list[str] | None = None,
        commands: list[str] | None = None,  # Deprecated, use command
    ):
        """
        Initialize command filter.

        Args:
            command: Command(s) to match (with or without leading /)
            commands: Deprecated - use command parameter instead
        """
        # Support legacy commands parameter
        if commands is not None:
            self.commands = commands if isinstance(commands, list) else [commands]
        elif command is not None:
            self.commands = command if isinstance(command, list) else [command]
        else:
            self.commands = []

        # Normalize commands (add leading / if missing)
        self.commands = [cmd if cmd.startswith("/") else f"/{cmd}" for cmd in self.commands]

    def check(self, update: Update) -> bool:
        message_text = update.text

        if not message_text:
            return False

        # Check if message starts with any command
        for command in self.commands:
            if message_text.startswith(command):
                # Command must be followed by space or end of string
                rest = message_text[len(command) :]
                return not rest or rest.startswith(" ") or rest.startswith("\n")

        return False


class CallbackDataFilter(Filter):
    """Filter by callback query data"""

    def __init__(self, callback_data: str | re.Pattern[str]):
        """
        Initialize callback data filter.

        Args:
            callback_data: Callback data to match (string or regex pattern)
        """
        self.callback_data = callback_data

    def check(self, update: Update) -> bool:
        # Check if update has callback_query
        callback_data = update.text

        if callback_data is None:
            return False

        if isinstance(self.callback_data, re.Pattern):
            return bool(self.callback_data.search(callback_data))

        return callback_data == self.callback_data


class ChatTypeFilter(Filter):
    """Filter by chat type (private, group, channel)"""

    def __init__(self, chat_type: str | list[str]):
        """
        Initialize chat type filter.

        Args:
            chat_type: Chat type(s) to match
        """
        self.chat_types = chat_type if isinstance(chat_type, list) else [chat_type]

    def check(self, update: Update) -> bool:
        return update.chat.type in self.chat_types
