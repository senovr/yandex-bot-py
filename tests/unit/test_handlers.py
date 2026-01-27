"""Unit tests for handlers"""
import pytest

from ymbot_async.dispatcher.handlers import (
    Handler,
    MessageHandler,
    CallbackQueryHandler,
)
from ymbot_async.dispatcher.filters import TextFilter, CommandFilter
from ymbot_async.api.schemas import Update, Message, Chat, User


class TestHandler:
    """Tests for base Handler class"""

    def test_handler_is_abstract(self):
        """Test that Handler cannot be instantiated directly"""
        with pytest.raises(TypeError):
            Handler()  # type: ignore


class TestMessageHandler:
    """Tests for MessageHandler"""

    @pytest.mark.asyncio
    async def test_message_handler_calls_callback(self, sample_update):
        """Test that MessageHandler calls callback"""
        async def callback(update):
            return "handled"

        handler = MessageHandler(callback)
        result = await handler.handle(sample_update)
        assert result == "handled"

    @pytest.mark.asyncio
    async def test_message_handler_with_no_filters(self, sample_update):
        """Test MessageHandler with no filters matches any message"""
        async def callback(update):
            return True

        handler = MessageHandler(callback, filters=None)
        assert handler.check(sample_update) is True

    @pytest.mark.asyncio
    async def test_message_handler_with_single_filter(self, sample_update):
        """Test MessageHandler with single filter"""
        sample_update.message.text = "Hello"
        
        async def callback(update):
            return True

        filter_obj = TextFilter(text="Hello")
        handler = MessageHandler(callback, filters=filter_obj)
        assert handler.check(sample_update) is True

    @pytest.mark.asyncio
    async def test_message_handler_with_filter_no_match(self, sample_update):
        """Test MessageHandler with filter that doesn't match"""
        sample_update.message.text = "Goodbye"
        
        async def callback(update):
            return True

        filter_obj = TextFilter(text="Hello")
        handler = MessageHandler(callback, filters=filter_obj)
        assert handler.check(sample_update) is False

    @pytest.mark.asyncio
    async def test_message_handler_with_multiple_filters(self, sample_update):
        """Test MessageHandler with list of filters"""
        sample_update.message.text = "/start"
        sample_update.message.chat = Chat(id="123", type="private", name="User")
        
        async def callback(update):
            return True

        filters = [
            CommandFilter(command="start"),
            TextFilter(text=None),
        ]
        handler = MessageHandler(callback, filters=filters)
        assert handler.check(sample_update) is True

    @pytest.mark.asyncio
    async def test_message_handler_multiple_filters_one_fails(self, sample_update):
        """Test MessageHandler with multiple filters where one fails"""
        sample_update.message.text = "Hello"
        sample_update.message.chat = Chat(id="123", type="private", name="User")
        
        async def callback(update):
            return True

        filters = [
            CommandFilter(command="start"),
            TextFilter(text=None),
        ]
        handler = MessageHandler(callback, filters=filters)
        assert handler.check(sample_update) is False

    @pytest.mark.asyncio
    async def test_message_handler_no_message(self):
        """Test MessageHandler with update without message"""
        async def callback(update):
            return True

        handler = MessageHandler(callback, filters=None)
        update = Update(update_id=1, message=None, callback_query=None)
        assert handler.check(update) is False

    @pytest.mark.asyncio
    async def test_message_handler_receives_update(self, sample_update):
        """Test that callback receives update"""
        received_update = None

        async def callback(update):
            nonlocal received_update
            received_update = update
            return "result"

        handler = MessageHandler(callback)
        await handler.handle(sample_update)
        assert received_update == sample_update

    @pytest.mark.asyncio
    async def test_message_handler_callback_exception(self, sample_update):
        """Test that exceptions in callback propagate"""
        async def callback(update):
            raise ValueError("Test error")

        handler = MessageHandler(callback)
        with pytest.raises(ValueError, match="Test error"):
            await handler.handle(sample_update)

    @pytest.mark.asyncio
    async def test_message_handler_callback_none_result(self, sample_update):
        """Test that callback can return None"""
        async def callback(update):
            return None

        handler = MessageHandler(callback)
        result = await handler.handle(sample_update)
        assert result is None


class TestCallbackQueryHandler:
    """Tests for CallbackQueryHandler"""

    @pytest.mark.asyncio
    async def test_callback_handler_calls_callback(self, sample_update):
        """Test that CallbackQueryHandler calls callback"""
        sample_update.message.text = "btn_click"
        
        async def callback(update):
            return "handled"

        handler = CallbackQueryHandler(callback)
        result = await handler.handle(sample_update)
        assert result == "handled"

    @pytest.mark.asyncio
    async def test_callback_handler_with_no_filters(self, sample_update):
        """Test CallbackQueryHandler with no filters"""
        sample_update.message.text = "data"
        
        async def callback(update):
            return True

        handler = CallbackQueryHandler(callback, filters=None)
        assert handler.check(sample_update) is True

    @pytest.mark.asyncio
    async def test_callback_handler_with_single_filter(self, sample_update):
        """Test CallbackQueryHandler with single filter"""
        sample_update.message.text = "btn_click"
        
        async def callback(update):
            return True

        from ymbot_async.dispatcher.filters import CallbackDataFilter
        filter_obj = CallbackDataFilter(callback_data="btn_click")
        handler = CallbackQueryHandler(callback, filters=filter_obj)
        assert handler.check(sample_update) is True

    @pytest.mark.asyncio
    async def test_callback_handler_with_filter_no_match(self, sample_update):
        """Test CallbackQueryHandler with filter that doesn't match"""
        sample_update.message.text = "btn_other"
        
        async def callback(update):
            return True

        from ymbot_async.dispatcher.filters import CallbackDataFilter
        filter_obj = CallbackDataFilter(callback_data="btn_click")
        handler = CallbackQueryHandler(callback, filters=filter_obj)
        assert handler.check(sample_update) is False

    @pytest.mark.asyncio
    async def test_callback_handler_with_multiple_filters(self, sample_update):
        """Test CallbackQueryHandler with list of filters"""
        sample_update.message.text = "btn_click"
        
        async def callback(update):
            return True

        from ymbot_async.dispatcher.filters import CallbackDataFilter, TextFilter
        filters = [
            CallbackDataFilter(callback_data="btn_click"),
            TextFilter(text=None),
        ]
        handler = CallbackQueryHandler(callback, filters=filters)
        assert handler.check(sample_update) is True

    @pytest.mark.asyncio
    async def test_callback_handler_multiple_filters_one_fails(self, sample_update):
        """Test CallbackQueryHandler with multiple filters where one fails"""
        sample_update.message.text = "btn_click"
        
        async def callback(update):
            return True

        from ymbot_async.dispatcher.filters import CallbackDataFilter, TextFilter
        filters = [
            CallbackDataFilter(callback_data="btn_click"),
            TextFilter(text="other"),
        ]
        handler = CallbackQueryHandler(callback, filters=filters)
        assert handler.check(sample_update) is False

    @pytest.mark.asyncio
    async def test_callback_handler_no_message(self):
        """Test CallbackQueryHandler with update without message"""
        async def callback(update):
            return True

        handler = CallbackQueryHandler(callback, filters=None)
        update = Update(update_id=1, message=None, callback_query=None)
        assert handler.check(update) is False

    @pytest.mark.asyncio
    async def test_callback_handler_no_text(self, sample_update):
        """Test CallbackQueryHandler with message but no text"""
        sample_update.message.text = ""
        
        async def callback(update):
            return True

        handler = CallbackQueryHandler(callback, filters=None)
        assert handler.check(sample_update) is False

    @pytest.mark.asyncio
    async def test_callback_handler_receives_update(self, sample_update):
        """Test that callback receives update"""
        received_update = None

        async def callback(update):
            nonlocal received_update
            received_update = update
            return "result"

        sample_update.message.text = "data"
        handler = CallbackQueryHandler(callback)
        await handler.handle(sample_update)
        assert received_update == sample_update

    @pytest.mark.asyncio
    async def test_callback_handler_callback_exception(self, sample_update):
        """Test that exceptions in callback propagate"""
        async def callback(update):
            raise ValueError("Test error")

        handler = CallbackQueryHandler(callback)
        with pytest.raises(ValueError, match="Test error"):
            await handler.handle(sample_update)

    @pytest.mark.asyncio
    async def test_callback_handler_callback_none_result(self, sample_update):
        """Test that callback can return None"""
        async def callback(update):
            return None

        handler = CallbackQueryHandler(callback)
        result = await handler.handle(sample_update)
        assert result is None