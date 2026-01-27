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
from ymbot_async.api.schemas import Update, Message, Chat, User


class TestTextFilter:
    """Tests for TextFilter"""

    def test_text_filter_with_exact_match(self, sample_message):
        """Test TextFilter with exact text match"""
        sample_message.text = "Hello"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = TextFilter(text="Hello")
        assert filter_obj.check(update) is True

    def test_text_filter_with_no_match(self, sample_message):
        """Test TextFilter with no match"""
        sample_message.text = "Hello"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = TextFilter(text="Goodbye")
        assert filter_obj.check(update) is False

    def test_text_filter_with_regex_match(self, sample_message):
        """Test TextFilter with regex pattern"""
        sample_message.text = "Hello World"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = TextFilter(text=re.compile(r"Hello.*"))
        assert filter_obj.check(update) is True

    def test_text_filter_with_regex_no_match(self, sample_message):
        """Test TextFilter with regex that doesn't match"""
        sample_message.text = "Hello World"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = TextFilter(text=re.compile(r"Goodbye.*"))
        assert filter_obj.check(update) is False

    def test_text_filter_none_matches_any_text(self, sample_message):
        """Test TextFilter with None matches any non-empty text"""
        sample_message.text = "Any text"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = TextFilter(text=None)
        assert filter_obj.check(update) is True

    def test_text_filter_none_no_text(self, sample_message):
        """Test TextFilter with None doesn't match empty text"""
        sample_message.text = ""
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = TextFilter(text=None)
        assert filter_obj.check(update) is False

    def test_text_filter_no_message(self):
        """Test TextFilter with no message in update"""
        update = Update(update_id=1, message=None, callback_query=None)
        filter_obj = TextFilter(text="Hello")
        assert filter_obj.check(update) is False


class TestCommandFilter:
    """Tests for CommandFilter"""

    def test_command_filter_with_command(self, sample_message):
        """Test CommandFilter matches command"""
        sample_message.text = "/start"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is True

    def test_command_filter_with_slash(self, sample_message):
        """Test CommandFilter matches command with leading slash"""
        sample_message.text = "/start"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command="/start")
        assert filter_obj.check(update) is True

    def test_command_filter_with_args(self, sample_message):
        """Test CommandFilter matches command with arguments"""
        sample_message.text = "/start arg1 arg2"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is True

    def test_command_filter_multiple_commands(self, sample_message):
        """Test CommandFilter with multiple commands"""
        sample_message.text = "/help"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command=["start", "help"])
        assert filter_obj.check(update) is True

    def test_command_filter_no_match(self, sample_message):
        """Test CommandFilter doesn't match wrong command"""
        sample_message.text = "/help"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_no_message(self):
        """Test CommandFilter with no message"""
        update = Update(update_id=1, message=None, callback_query=None)
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_no_text(self, sample_message):
        """Test CommandFilter with no text"""
        sample_message.text = ""
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_command_in_middle(self, sample_message):
        """Test CommandFilter doesn't match command in middle of text"""
        sample_message.text = "text /start more"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False

    def test_command_filter_deprecated_commands_param(self, sample_message):
        """Test CommandFilter with deprecated commands parameter"""
        sample_message.text = "/start"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(commands="start")
        assert filter_obj.check(update) is True

    def test_command_filter_case_sensitive(self, sample_message):
        """Test CommandFilter is case sensitive"""
        sample_message.text = "/START"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CommandFilter(command="start")
        assert filter_obj.check(update) is False


class TestCallbackDataFilter:
    """Tests for CallbackDataFilter"""

    def test_callback_data_filter_with_string(self, sample_message):
        """Test CallbackDataFilter with exact string match"""
        sample_message.text = "btn_click"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CallbackDataFilter(callback_data="btn_click")
        assert filter_obj.check(update) is True

    def test_callback_data_filter_no_match(self, sample_message):
        """Test CallbackDataFilter with no match"""
        sample_message.text = "btn_click"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CallbackDataFilter(callback_data="btn_other")
        assert filter_obj.check(update) is False

    def test_callback_data_filter_with_regex(self, sample_message):
        """Test CallbackDataFilter with regex pattern"""
        sample_message.text = "btn_click_123"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CallbackDataFilter(callback_data=re.compile(r"btn_click.*"))
        assert filter_obj.check(update) is True

    def test_callback_data_filter_regex_no_match(self, sample_message):
        """Test CallbackDataFilter with regex that doesn't match"""
        sample_message.text = "btn_click"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = CallbackDataFilter(callback_data=re.compile(r"btn_other.*"))
        assert filter_obj.check(update) is False

    def test_callback_data_filter_no_message(self):
        """Test CallbackDataFilter with no message"""
        update = Update(update_id=1, message=None, callback_query=None)
        filter_obj = CallbackDataFilter(callback_data="btn_click")
        assert filter_obj.check(update) is False


class TestChatTypeFilter:
    """Tests for ChatTypeFilter"""

    def test_chat_type_filter_private(self, sample_message):
        """Test ChatTypeFilter matches private chat"""
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = ChatTypeFilter(chat_type="private")
        assert filter_obj.check(update) is True

    def test_chat_type_filter_group(self, sample_message):
        """Test ChatTypeFilter matches group chat"""
        sample_message.chat = Chat(id="123", type="group", name="Group")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = ChatTypeFilter(chat_type="group")
        assert filter_obj.check(update) is True

    def test_chat_type_filter_channel(self, sample_message):
        """Test ChatTypeFilter matches channel"""
        sample_message.chat = Chat(id="123", type="channel", name="Channel")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = ChatTypeFilter(chat_type="channel")
        assert filter_obj.check(update) is True

    def test_chat_type_filter_multiple_types(self, sample_message):
        """Test ChatTypeFilter with multiple chat types"""
        sample_message.chat = Chat(id="123", type="group", name="Group")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = ChatTypeFilter(chat_type=["private", "group"])
        assert filter_obj.check(update) is True

    def test_chat_type_filter_no_match(self, sample_message):
        """Test ChatTypeFilter doesn't match wrong type"""
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter_obj = ChatTypeFilter(chat_type="group")
        assert filter_obj.check(update) is False

    def test_chat_type_filter_no_message(self):
        """Test ChatTypeFilter with no message"""
        update = Update(update_id=1, message=None, callback_query=None)
        filter_obj = ChatTypeFilter(chat_type="private")
        assert filter_obj.check(update) is False


class TestAndFilter:
    """Tests for AndFilter"""

    def test_and_filter_both_match(self, sample_message):
        """Test AndFilter when both filters match"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        and_filter = text_filter & chat_filter
        assert and_filter.check(update) is True

    def test_and_filter_one_matches(self, sample_message):
        """Test AndFilter when only one filter matches"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="group", name="Group")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        and_filter = text_filter & chat_filter
        assert and_filter.check(update) is False

    def test_and_filter_none_match(self, sample_message):
        """Test AndFilter when neither filter matches"""
        sample_message.text = "Goodbye"
        sample_message.chat = Chat(id="123", type="group", name="Group")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        and_filter = text_filter & chat_filter
        assert and_filter.check(update) is False

    def test_and_filter_multiple_filters(self, sample_message):
        """Test AndFilter with more than two filters"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter1 = TextFilter(text="Hello")
        filter2 = ChatTypeFilter(chat_type="private")
        filter3 = TextFilter(text=None)  # Non-empty text
        and_filter = AndFilter(filter1, filter2, filter3)
        assert and_filter.check(update) is True


class TestOrFilter:
    """Tests for OrFilter"""

    def test_or_filter_both_match(self, sample_message):
        """Test OrFilter when both filters match"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        or_filter = text_filter | chat_filter
        assert or_filter.check(update) is True

    def test_or_filter_one_matches(self, sample_message):
        """Test OrFilter when only one filter matches"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="group", name="Group")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        or_filter = text_filter | chat_filter
        assert or_filter.check(update) is True

    def test_or_filter_none_match(self, sample_message):
        """Test OrFilter when neither filter matches"""
        sample_message.text = "Goodbye"
        sample_message.chat = Chat(id="123", type="group", name="Group")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="private")
        or_filter = text_filter | chat_filter
        assert or_filter.check(update) is False

    def test_or_filter_multiple_filters(self, sample_message):
        """Test OrFilter with more than two filters"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="group", name="Group")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        filter1 = TextFilter(text="Hello")
        filter2 = TextFilter(text="Goodbye")
        filter3 = ChatTypeFilter(chat_type="private")
        or_filter = OrFilter(filter1, filter2, filter3)
        assert or_filter.check(update) is True


class TestNotFilter:
    """Tests for NotFilter"""

    def test_not_filter_inverts_true(self, sample_message):
        """Test NotFilter inverts True to False"""
        sample_message.text = "Hello"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        not_filter = ~text_filter
        assert not_filter.check(update) is False

    def test_not_filter_inverts_false(self, sample_message):
        """Test NotFilter inverts False to True"""
        sample_message.text = "Goodbye"
        update = Update(update_id=1, message=sample_message, callback_query=None)
        text_filter = TextFilter(text="Hello")
        not_filter = ~text_filter
        assert not_filter.check(update) is True


class TestFilterComposition:
    """Tests for complex filter composition"""

    def test_complex_and_or_combination(self, sample_message):
        """Test complex AND/OR filter combination"""
        sample_message.text = "/start"
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        
        cmd_filter = CommandFilter(command="start")
        private_filter = ChatTypeFilter(chat_type="private")
        group_filter = ChatTypeFilter(chat_type="group")
        
        # (command AND private) OR group
        combined = (cmd_filter & private_filter) | group_filter
        assert combined.check(update) is True

    def test_nested_negation(self, sample_message):
        """Test nested filter negation"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        
        text_filter = TextFilter(text="Hello")
        chat_filter = ChatTypeFilter(chat_type="group")
        
        # text AND NOT group
        combined = text_filter & ~chat_filter
        assert combined.check(update) is True

    def test_chained_and(self, sample_message):
        """Test chained AND operations"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        
        filter1 = TextFilter(text="Hello")
        filter2 = ChatTypeFilter(chat_type="private")
        filter3 = TextFilter(text=None)
        
        combined = filter1 & filter2 & filter3
        assert combined.check(update) is True

    def test_chained_or(self, sample_message):
        """Test chained OR operations"""
        sample_message.text = "Hello"
        sample_message.chat = Chat(id="123", type="private", name="User")
        update = Update(update_id=1, message=sample_message, callback_query=None)
        
        filter1 = TextFilter(text="Hello")
        filter2 = TextFilter(text="Goodbye")
        filter3 = TextFilter(text="Test")
        
        combined = filter1 | filter2 | filter3
        assert combined.check(update) is True
