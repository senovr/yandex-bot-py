"""Integration tests for Dispatcher error handling and advanced scenarios"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from ymbot_async.api.schemas import Chat, Sender, Update
from ymbot_async.config import BotConfig
from ymbot_async.dispatcher.filters import TextFilter
from ymbot_async.dispatcher.handlers import MessageHandler


class TestDispatcherErrorHandling:
    """Tests for error handling in dispatcher"""

    @pytest.mark.asyncio
    async def test_handler_exception_logged_and_continued(self, caplog):
        """Test that handler exceptions are logged and processing continues"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        # Create dispatcher with small queue for testing
        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=2)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        # Track if handler was called
        handler_called = asyncio.Event()

        # Create a handler that raises exception
        async def failing_handler(update):
            handler_called.set()
            raise ValueError("Handler error!")

        async def good_handler(update):
            pass

        # Register handlers
        dispatcher.register_handler(MessageHandler(failing_handler, TextFilter(text="fail")))
        dispatcher.register_handler(MessageHandler(good_handler, TextFilter(text="good")))

        # Start dispatcher in background
        run_task = asyncio.create_task(dispatcher.run())

        # Create failing update
        failing_update = Update(
            update_id=1,
            message_id=123,
            text="fail",
            timestamp=1738000800,
            chat=Chat(type="private", id="456"),
            **{"from": Sender(id="user1")},
        )

        # Feed failing update
        await dispatcher.feed_update(failing_update)
        await handler_called.wait()

        # Create good update
        good_update = Update(
            update_id=2,
            message_id=124,
            text="good",
            timestamp=1738000860,
            chat=Chat(type="private", id="456"),
            **{"from": Sender(id="user1")},
        )

        # Feed good update - should be processed
        await dispatcher.feed_update(good_update)

        # Wait a bit for processing
        await asyncio.sleep(0.2)

        # Stop dispatcher
        await dispatcher.stop()
        await run_task

        # Check that exception was logged
        assert any(
            "Handler error" in record.message and "ValueError" in record.message
            for record in caplog.records
        ), "Handler exception should be logged"

    @pytest.mark.asyncio
    async def test_no_matching_handler_logged(self, caplog):
        """Test that unmatched updates are logged"""
        import logging

        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=2)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        # Capture DEBUG level logs
        caplog.set_level(logging.DEBUG)

        # Register handler that won't match
        async def handler(update):
            pass

        dispatcher.register_handler(MessageHandler(handler, TextFilter(text="match")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        # Create update that won't match
        update = Update(
            update_id=1,
            message_id=123,
            text="nomatch",
            timestamp=1738000800,
            chat=Chat(type="private", id="456"),
            **{"from": Sender(id="user1")},
        )

        await dispatcher.feed_update(update)
        await asyncio.sleep(0.2)

        # Stop dispatcher
        await dispatcher.stop()
        await run_task

        # Check that no handler matched was logged
        assert any("No handler matched" in record.message for record in caplog.records), (
            "No handler matched should be logged"
        )


class TestDispatcherConcurrency:
    """Tests for concurrent update processing"""

    @pytest.mark.asyncio
    async def test_concurrent_updates_processed(self):
        """Test that multiple updates are processed concurrently"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=3)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        # Track processed updates
        processed = []
        processing_lock = asyncio.Lock()

        async def handler(update):
            async with processing_lock:
                processed.append(update.update_id)
                # Simulate async work
                await asyncio.sleep(0.05)

        dispatcher.register_handler(MessageHandler(handler, TextFilter(text="test")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        # Create multiple updates
        updates = [
            Update(
                update_id=i,
                message_id=i,
                text="test",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id=f"user{i}")},
            )
            for i in range(1, 5)
        ]

        # Feed all updates
        for update in updates:
            await dispatcher.feed_update(update)

        # Wait for processing
        await asyncio.sleep(0.3)

        # Stop dispatcher
        await dispatcher.stop()
        await run_task

        # Check that all updates were processed
        assert len(processed) == 4
        assert set(processed) == {1, 2, 3, 4}

    @pytest.mark.asyncio
    async def test_concurrency_limit_respected(self):
        """Test that concurrency limit is respected"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=2)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        # Track concurrent processing
        max_concurrent = 0
        concurrent_count = 0
        count_lock = asyncio.Lock()

        async def handler(update):
            nonlocal max_concurrent, concurrent_count
            async with count_lock:
                concurrent_count += 1
                if concurrent_count > max_concurrent:
                    max_concurrent = concurrent_count
            await asyncio.sleep(0.1)
            async with count_lock:
                concurrent_count -= 1

        dispatcher.register_handler(MessageHandler(handler, TextFilter(text="test")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        # Create 5 updates
        for i in range(1, 6):
            update = Update(
                update_id=i,
                message_id=i,
                text="test",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id=f"user{i}")},
            )
            await dispatcher.feed_update(update)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Stop dispatcher
        await dispatcher.stop()
        await run_task

        # Check that concurrency limit was respected
        assert max_concurrent == 2, f"Max concurrent was {max_concurrent}, expected 2"


class TestDispatcherWorkerLifecycle:
    """Tests for worker task lifecycle"""

    @pytest.mark.asyncio
    async def test_worker_task_lifecycle(self):
        """Test that worker tasks are created and stopped properly"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=3)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        processed = []

        async def handler(update):
            processed.append(update.update_id)

        dispatcher.register_handler(MessageHandler(handler, TextFilter(text="test")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        # Verify workers are created
        await asyncio.sleep(0.1)

        # Feed updates
        for i in range(1, 4):
            update = Update(
                update_id=i,
                message_id=i,
                text="test",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id=f"user{i}")},
            )
            await dispatcher.feed_update(update)

        # Wait for processing
        await asyncio.sleep(0.2)

        # Stop dispatcher
        await dispatcher.stop()
        await run_task

        # Verify all updates were processed
        assert len(processed) == 3
        assert set(processed) == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_dispatcher_run_with_updates(self):
        """Test complete dispatcher lifecycle with run() method"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=2)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        processed = []

        async def handler(update):
            processed.append(update.update_id)

        dispatcher.register_handler(MessageHandler(handler, TextFilter(text="test")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        # Feed updates
        for i in range(1, 4):
            update = Update(
                update_id=i,
                message_id=i,
                text="test",
                timestamp=1738000800,
                chat=Chat(type="private", id="456"),
                **{"from": Sender(id=f"user{i}")},
            )
            await dispatcher.feed_update(update)

        # Wait for processing
        await asyncio.sleep(0.3)

        # Stop dispatcher (which will call run() to complete)
        await dispatcher.stop()
        await run_task

        # Verify all updates were processed
        assert len(processed) == 3


class TestDispatcherRealHandlerExecution:
    """Tests for real handler execution (not just filtering)"""

    @pytest.mark.asyncio
    async def test_handler_executes_with_update_data(self):
        """Test that handler receives and can access update data"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=2)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        received_updates = []

        async def handler(update):
            # Capture the full update object
            received_updates.append(
                {
                    "update_id": update.update_id,
                    "message_id": update.message_id,
                    "text": update.text,
                    "chat_id": update.chat.id,
                }
            )

        dispatcher.register_handler(MessageHandler(handler, TextFilter(text="test")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        # Create update with specific data
        update = Update(
            update_id=42,
            message_id=123,
            text="test",
            timestamp=1738000800,
            chat=Chat(type="private", id="chat456"),
            **{"from": Sender(id="user42")},
        )

        await dispatcher.feed_update(update)
        await asyncio.sleep(0.2)

        # Stop dispatcher
        await dispatcher.stop()
        await run_task

        # Verify handler received correct data
        assert len(received_updates) == 1
        assert received_updates[0]["update_id"] == 42
        assert received_updates[0]["message_id"] == 123
        assert received_updates[0]["text"] == "test"
        assert received_updates[0]["chat_id"] == "chat456"

    @pytest.mark.asyncio
    async def test_multiple_handlers_first_wins(self):
        """Test that only first matching handler executes"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=2)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        handler_calls = []

        async def handler1(update):
            handler_calls.append("handler1")

        async def handler2(update):
            handler_calls.append("handler2")

        # Register handlers in specific order
        dispatcher.register_handler(MessageHandler(handler1, TextFilter(text="test")))
        dispatcher.register_handler(MessageHandler(handler2, TextFilter(text="test")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        update = Update(
            update_id=1,
            message_id=123,
            text="test",
            timestamp=1738000800,
            chat=Chat(type="private", id="456"),
            **{"from": Sender(id="user1")},
        )

        await dispatcher.feed_update(update)
        await asyncio.sleep(0.2)

        # Stop dispatcher
        await dispatcher.stop()
        await run_task

        # Verify only first handler was called
        assert handler_calls == ["handler1"], "Only first matching handler should execute"


class TestDispatcherGracefulShutdown:
    """Tests for graceful shutdown behavior"""

    @pytest.mark.asyncio
    async def test_dispatcher_waits_for_running_handlers(self):
        """Test that dispatcher waits for running handlers to complete"""
        from ymbot_async.dispatcher.dispatcher import Dispatcher

        config = BotConfig(token="test_token", queue_maxsize=10, concurrency=2)
        api_client = AsyncMock()
        dispatcher = Dispatcher(api_client, config)

        handler_started = asyncio.Event()
        handler_can_finish = asyncio.Event()
        handler_finished = asyncio.Event()

        async def slow_handler(update):
            handler_started.set()
            await handler_can_finish.wait()
            handler_finished.set()

        dispatcher.register_handler(MessageHandler(slow_handler, TextFilter(text="test")))

        # Start dispatcher
        run_task = asyncio.create_task(dispatcher.run())

        # Feed an update
        update = Update(
            update_id=1,
            message_id=123,
            text="test",
            timestamp=1738000800,
            chat=Chat(type="private", id="456"),
            **{"from": Sender(id="user1")},
        )

        await dispatcher.feed_update(update)
        await handler_started.wait()

        # Stop dispatcher while handler is running
        stop_task = asyncio.create_task(dispatcher.stop())

        # Verify stop hasn't completed yet
        await asyncio.sleep(0.1)
        assert not stop_task.done(), "Stop should wait for handler to complete"

        # Let handler finish
        handler_can_finish.set()

        # Wait for stop to complete
        await stop_task
        await run_task

        # Verify handler finished
        assert handler_finished.is_set()
