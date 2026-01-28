"""Unit tests for filters"""
import re

import pytest

from ymbot_async.dispatcher.filters import (
    Filter,
    AndFilter,
    OrFilter,
    NotFilter,
    TextFilter,
    CommandFilter,
    CallbackDataFilter,
    ChatTypeFilter,
)
from ymbot_async.api.schemas import Update, Chat, Sender


class TestTextFilter:
    """Tests for TextFilter"""

    def test_text_filter_with_exact_match(self):
        """Test TextFilter with exact text match"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter_obj = TextFilter(text="Hello")
        assert filter_obj.check(update) is True

    def test_text_filter_with_no_match(self):
        """Test TextFilter with no match"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter_obj = TextFilter(text="Goodbye")
        assert filter_obj.check(update) is False

    def test_text_filter_with_regex_match(self):
        """Test TextFilter with regex pattern"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello World",
        )
        filter_obj = TextFilter(text=re.compile(r"Hello.*"))
        assert filter_obj.check(update) is True

    def test_text_filter_with_regex_no_match(self):
        """Test TextFilter with regex that doesn't match"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello World",
        )
        filter_obj = TextFilter(text=re.compile(r"Goodbye.*"))
        assert filter_obj.check(update) is False

    def test_text_filter_none_matches_any_text(self):
        """Test TextFilter with None matches any non-empty text"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Any text",
        )
        filter_obj = TextFilter(text=None)
        assert filter_obj.check(update) is True

    def test_text_filter_none_no_text(self):
        """Test TextFilter with None doesn't match empty text"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="",
        )
        filter_obj = TextFilter(text=None)
        assert filter_obj.check(update) is False

    def test_text_filter_no_message(self):
        """Test TextFilter with no message in update"""
        # Update with no text field (empty update)
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text=None,
        )
        filter_obj = TextFilter(text="Hello")
        assert filter_obj.check(update) is False


class TestCommandFilter:
    """Tests for CommandFilter"""

    def test_command_filter_with_command(self):
        """Test CommandFilter matches command"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/start",
        )
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is True

    def test_command_filter_with_slash(self):
        """Test CommandFilter matches command with leading slash"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/start",
        )
        filter_obj = CommandFilter(command="/start")
        assert filter_obj.check(update) is True

    def test_command_filter_with_args(self):
        """Test CommandFilter matches command with arguments"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/start arg1 arg2",
        )
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is True

    def test_command_filter_multiple_commands(self):
        """Test CommandFilter with multiple commands"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/help",
        )
        filter_obj = CommandFilter(command=["start", "help"])
        assert filter_obj.check(update) is True

    def test_command_filter_no_match(self):
        """Test CommandFilter doesn't match wrong command"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/help",
        )
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_no_message(self):
        """Test CommandFilter with no message"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="",
        )
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_no_text(self):
        """Test CommandFilter with no text"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="",
        )
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_command_in_middle(self):
        """Test CommandFilter doesn't match command in middle of text"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="text /start more",
        )
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_deprecated_commands_param(self):
        """Test CommandFilter with deprecated commands parameter"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/start",
        )
        filter_obj = CommandFilter(commands="start")
        assert filter_obj.check(update) is True

    def test_command_filter_case_sensitive(self):
        """Test CommandFilter is case sensitive"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/START",
        )
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False


class TestCallbackDataFilter:
    """Tests for CallbackDataFilter"""

    def test_callback_data_filter_with_string(self):
        """Test CallbackDataFilter with exact string match"""
        # Note: Yandex API doesn't have callback_query, so this test is for potential future use
        # or for testing filter behavior with text field
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="btn_click",
        )
        filter_obj = CallbackDataFilter(callback_data="btn_click")
        assert filter_obj.check(update) is True

    def test_callback_data_filter_no_match(self):
        """Test CallbackDataFilter with no match"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="btn_click",
        )
        filter_obj = CallbackDataFilter(callback_data="btn_other")
        assert filter_obj.check(update) is False

    def test_callback_data_filter_with_regex(self):
        """Test CallbackDataFilter with regex pattern"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="btn_click_123",
        )
        filter_obj = CallbackDataFilter(callback_data=re.compile(r"btn_click.*"))
        assert filter_obj.check(update) is True

    def test_callback_data_filter_regex_no_match(self):
        """Test CallbackDataFilter with regex that doesn't match"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="btn_click",
        )
        filter_obj = CallbackDataFilter(callback_data=re.compile(r"btn_other.*"))
        assert filter_obj.check(update) is False

    def test_callback_data_filter_no_message(self):
        """Test CallbackDataFilter with no message"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text=None,
        )
        filter_obj = CallbackDataFilter(callback_data="btn_click")
        assert filter_obj.check(update) is False


class TestChatTypeFilter:
    """Tests for ChatTypeFilter"""

    def test_chat_type_filter_private(self):
        """Test ChatTypeFilter matches private chat"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter_obj = ChatTypeFilter(chat_type="private")
        assert filter_obj.check(update) is True

    def test_chat_type_filter_group(self):
        """Test ChatTypeFilter matches group chat"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="group"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter_obj = ChatTypeFilter(chat_type="group")
        assert filter_obj.check(update) is True

    def test_chat_type_filter_channel(self):
        """Test ChatTypeFilter matches channel"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="channel"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter_obj = ChatTypeFilter(chat_type="channel")
        assert filter_obj.check(update) is True

    def test_chat_type_filter_multiple_types(self):
        """Test ChatTypeFilter with multiple chat types"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="group"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter_obj = ChatTypeFilter(chat_type=["private", "group"])
        assert filter_obj.check(update) is True

    def test_chat_type_filter_no_match(self):
        """Test ChatTypeFilter doesn't match wrong type"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter_obj = ChatTypeFilter(chat_type="group")
        assert filter_obj.check(update) is False

    def test_chat_type_filter_no_message(self):
        """Test ChatTypeFilter with no message (text=None)"""
        # In Yandex API, chat field exists even when text is None
        # So ChatTypeFilter will still match the chat type
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text=None,
        )
        filter_obj = ChatTypeFilter(chat_type="private")
        assert filter_obj.check(update) is True


class TestAndFilter:
    """Tests for AndFilter"""

    def test_and_filter_both_match(self):
        """Test AndFilter when both filters match"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        and_filter = text_filter & chat_filter
        assert and_filter.check(update) is True

    def test_and_filter_one_matches(self):
        """Test AndFilter when only one filter matches"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="group"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        and_filter = text_filter & chat_filter
        assert and_filter.check(update) is False

    def test_and_filter_none_match(self):
        """Test AndFilter when neither filter matches"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="group"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Goodbye",
        )
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        and_filter = text_filter & chat_filter
        assert and_filter.check(update) is False

    def test_and_filter_multiple_filters(self):
        """Test AndFilter with more than two filters"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter1 = TextFilter(text="Hello")
        filter2 = ChatTypeFilter(chat_type="private")
        filter3 = TextFilter(text=None)  # Non-empty text
        and_filter = AndFilter(filter1, filter2, filter3)
        assert and_filter.check(update) is True


class TestOrFilter:
    """Tests for OrFilter"""

    def test_or_filter_both_match(self):
        """Test OrFilter when both filters match"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        or_filter = text_filter | chat_filter
        assert or_filter.check(update) is True

    def test_or_filter_one_matches(self):
        """Test OrFilter when only one filter matches"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="group"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        or_filter = text_filter | chat_filter
        assert or_filter.check(update) is True

    def test_or_filter_none_match(self):
        """Test OrFilter when neither filter matches"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="group"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Goodbye",
        )
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        or_filter = text_filter | chat_filter
        assert or_filter.check(update) is False

    def test_or_filter_multiple_filters(self):
        """Test OrFilter with more than two filters"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="group"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        filter1 = TextFilter(text="Hello")
        filter2 = TextFilter(text="Goodbye")
        filter3 = ChatTypeFilter(chat_type="private")
        or_filter = OrFilter(filter1, filter2, filter3)
        assert or_filter.check(update) is True


class TestNotFilter:
    """Tests for NotFilter"""

    def test_not_filter_inverts_true(self):
        """Test NotFilter inverts True to False"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        text_filter = TextFilter(text="Hello")
        not_filter = ~text_filter
        assert not_filter.check(update) is False

    def test_not_filter_inverts_false(self):
        """Test NotFilter inverts False to True"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Goodbye",
        )
        text_filter = TextFilter(text="Hello")
        not_filter = ~text_filter
        assert not_filter.check(update) is True


class TestFilterComposition:
    """Tests for complex filter composition"""

    def test_complex_and_or_combination(self):
        """Test complex AND/OR filter combination"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="/start",
        )
        
        cmd_filter = CommandFilter(command="start")
        private_filter = ChatTypeFilter(chat_type="private")
        group_filter = ChatTypeFilter(chat_type="group")
        
        # (command AND private) OR group
        combined = (cmd_filter & private_filter) | group_filter
        assert combined.check(update) is True

    def test_nested_negation(self):
        """Test nested filter negation"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="group")
        
        # text AND NOT group
        combined = text_filter & ~chat_filter
        assert combined.check(update) is True

    def test_chained_and(self):
        """Test chained AND operations"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        
        filter1 = TextFilter(text="Hello")
        filter2 = ChatTypeFilter(chat_type="private")
        filter3 = TextFilter(text=None)
        
        combined = filter1 & filter2 & filter3
        assert combined.check(update) is True

    def test_chained_or(self):
        """Test chained OR operations"""
        update = Update(
            update_id=1,
            message_id=1,
            timestamp=1704067200,
            chat=Chat(type="private"),
            **{"from": Sender(login="12345", display_name="Test User")},
            text="Hello",
        )
        
        filter1 = TextFilter(text="Hello")
        filter2 = TextFilter(text="Goodbye")
        filter3 = TextFilter(text="Test")
        
        combined = filter1 | filter2 | filter3
        assert combined.check(update) is True
