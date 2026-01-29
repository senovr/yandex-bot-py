"""Unit tests for Dispatcher"""

import asyncio
import dataclasses

import pytest

from ymbot_async.dispatcher.dispatcher import Dispatcher
from ymbot_async.dispatcher.handlers import Handler


class MockHandler(Handler):
    """Mock handler for testing"""

    def __init__(self, should_match=True):
        self.should_match = should_match
        self.calls = []

    def check(self, update):  # noqa: ARG002
        return self.should_match

    async def handle(self, update):
        self.calls.append(update)
        await asyncio.sleep(0.01)  # Simulate async work


class TestDispatcherInit:
    """Tests for Dispatcher initialization"""

    def test_dispatcher_initializes_with_config(self, bot_config):
        """Test dispatcher uses config for initialization"""
        dispatcher = Dispatcher(bot_config)

        assert dispatcher.config == bot_config
        assert dispatcher.handlers == []
        assert dispatcher._stopped is False

    def test_dispatcher_initializes_queue(self, bot_config):
        """Test dispatcher initializes queue with maxsize from config"""
        dispatcher = Dispatcher(bot_config)

        assert dispatcher._update_queue.maxsize == bot_config.queue_maxsize

    def test_dispatcher_initializes_semaphore(self, bot_config):
        """Test dispatcher initializes semaphore with concurrency limit"""
        dispatcher = Dispatcher(bot_config)

        assert dispatcher._concurrency_semaphore._value == bot_config.concurrency


class TestDispatcherRegisterHandler:
    """Tests for register_handler method"""

    @pytest.mark.asyncio
    async def test_register_handler_adds_to_list(self, bot_config):
        """Test register_handler adds handler to list"""
        dispatcher = Dispatcher(bot_config)
        handler = MockHandler()

        dispatcher.register_handler(handler)

        assert len(dispatcher.handlers) == 1
        assert dispatcher.handlers[0] == handler

    @pytest.mark.asyncio
    async def test_register_multiple_handlers(self, bot_config):
        """Test registering multiple handlers"""
        dispatcher = Dispatcher(bot_config)
        handler1 = MockHandler()
        handler2 = MockHandler()

        dispatcher.register_handler(handler1)
        dispatcher.register_handler(handler2)

        assert len(dispatcher.handlers) == 2
        assert dispatcher.handlers[0] == handler1
        assert dispatcher.handlers[1] == handler2


class TestDispatcherFeedUpdate:
    """Tests for feed_update method"""

    @pytest.mark.asyncio
    async def test_feed_update_adds_to_queue(self, bot_config, sample_update):
        """Test feed_update adds update to queue"""
        dispatcher = Dispatcher(bot_config)

        result = await dispatcher.feed_update(sample_update)

        assert result is True
        assert dispatcher._update_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_feed_update_when_queue_full(self, bot_config, sample_update):
        """Test feed_update returns False when queue is full"""
        config = dataclasses.replace(bot_config, queue_maxsize=2)
        dispatcher = Dispatcher(config)

        # Fill queue
        await dispatcher.feed_update(sample_update)
        await dispatcher.feed_update(sample_update)

        # Try to add more
        result = await dispatcher.feed_update(sample_update)

        assert result is False
        assert dispatcher._update_queue.qsize() == 2

    @pytest.mark.asyncio
    async def test_feed_update_when_stopped(self, bot_config, sample_update):
        """Test feed_update returns False when dispatcher is stopped"""
        dispatcher = Dispatcher(bot_config)
        dispatcher._stopped = True

        result = await dispatcher.feed_update(sample_update)

        assert result is False


class TestDispatcherProcessUpdate:
    """Tests for _process_update method"""

    @pytest.mark.asyncio
    async def test_process_update_calls_handler(self, bot_config, sample_update):
        """Test _process_update calls matching handler"""
        dispatcher = Dispatcher(bot_config)
        handler = MockHandler(should_match=True)
        dispatcher.handlers = [handler]

        await dispatcher._process_update(sample_update)

        assert len(handler.calls) == 1
        assert handler.calls[0] == sample_update

    @pytest.mark.asyncio
    async def test_process_update_no_matching_handler(self, bot_config, sample_update):
        """Test _process_update with no matching handler"""
        dispatcher = Dispatcher(bot_config)
        handler = MockHandler(should_match=False)
        dispatcher.handlers = [handler]

        await dispatcher._process_update(sample_update)

        assert len(handler.calls) == 0

    @pytest.mark.asyncio
    async def test_process_update_first_handler_wins(self, bot_config, sample_update):
        """Test first matching handler is executed"""
        dispatcher = Dispatcher(bot_config)
        handler1 = MockHandler(should_match=True)
        handler2 = MockHandler(should_match=True)
        dispatcher.handlers = [handler1, handler2]

        await dispatcher._process_update(sample_update)

        assert len(handler1.calls) == 1
        assert len(handler2.calls) == 0

    @pytest.mark.asyncio
    async def test_process_update_handler_exception(self, bot_config, sample_update):
        """Test _process_update handles handler exceptions"""
        dispatcher = Dispatcher(bot_config)

        class FailingHandler(Handler):
            def check(self, update):  # noqa: ARG002
                return True

            async def handle(self, update):  # noqa: ARG002
                raise ValueError("Handler error")

        handler = FailingHandler()
        dispatcher.handlers = [handler]

        # Should not raise exception
        await dispatcher._process_update(sample_update)


class TestDispatcherConcurrency:
    """Tests for concurrency control"""

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, bot_config, sample_update):
        """Test dispatcher respects concurrency limit"""
        config = dataclasses.replace(bot_config, concurrency=2, queue_maxsize=10)
        dispatcher = Dispatcher(config)

        processed = []

        class SlowHandler(Handler):
            def check(self, update):  # noqa: ARG002
                return True

            async def handle(self, update):  # noqa: ARG002
                processed.append(1)
                await asyncio.sleep(0.2)

        dispatcher.handlers = [SlowHandler()]

        # Feed multiple updates
        for _ in range(5):
            await dispatcher.feed_update(sample_update)

        # Start processing in background
        run_task = asyncio.create_task(dispatcher.run())

        # Wait a bit
        await asyncio.sleep(0.1)

        # At most 2 should be processed at this point (concurrency limit)
        assert len(processed) <= 2

        # Stop dispatcher
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=2.0)

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_tasks(self, bot_config, sample_update):
        """Test semaphore limits concurrent handler execution"""
        config = dataclasses.replace(bot_config, concurrency=2, queue_maxsize=10)
        dispatcher = Dispatcher(config)

        concurrent_count = 0
        max_concurrent = 0

        class CountingHandler(Handler):
            def check(self, update):  # noqa: ARG002
                return True

            async def handle(self, update):  # noqa: ARG002
                nonlocal concurrent_count, max_concurrent
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
                await asyncio.sleep(0.1)
                concurrent_count -= 1

        dispatcher.handlers = [CountingHandler()]

        # Feed multiple updates and process concurrently
        run_task = asyncio.create_task(dispatcher.run())

        for _ in range(5):
            await dispatcher.feed_update(sample_update)

        # Wait for processing
        await asyncio.sleep(0.2)

        # Stop dispatcher
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=2.0)

        # At most 2 should run concurrently
        assert max_concurrent <= 2


class TestDispatcherWorker:
    """Tests for worker tasks"""

    @pytest.mark.asyncio
    async def test_worker_processes_updates(self, bot_config, sample_update):
        """Test worker processes updates from queue"""
        config = dataclasses.replace(bot_config, concurrency=1)
        dispatcher = Dispatcher(config)

        handler = MockHandler(should_match=True)
        dispatcher.handlers = [handler]

        # Feed update
        await dispatcher.feed_update(sample_update)

        # Run dispatcher
        run_task = asyncio.create_task(dispatcher.run())
        await asyncio.sleep(0.1)

        # Stop dispatcher
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        assert len(handler.calls) == 1

    @pytest.mark.asyncio
    async def test_worker_stops_on_shutdown(self, bot_config):
        """Test worker stops on shutdown signal"""
        config = dataclasses.replace(bot_config, concurrency=1)
        dispatcher = Dispatcher(config)

        # Run dispatcher
        run_task = asyncio.create_task(dispatcher.run())
        await asyncio.sleep(0.05)

        # Stop dispatcher
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        assert run_task.done()

    @pytest.mark.asyncio
    async def test_worker_times_out_waiting_for_update(self, bot_config):
        """Test worker timeout when waiting for update"""
        config = dataclasses.replace(bot_config, concurrency=1)
        dispatcher = Dispatcher(config)

        # Don't feed any updates, just run
        run_task = asyncio.create_task(dispatcher.run())

        # Wait a bit (should timeout waiting for update)
        await asyncio.sleep(0.2)

        # Signal shutdown
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        assert run_task.done()


class TestDispatcherStop:
    """Tests for stop method"""

    @pytest.mark.asyncio
    async def test_stop_sets_stopped_flag(self, bot_config):
        """Test stop sets stopped flag"""
        dispatcher = Dispatcher(bot_config)

        await dispatcher.stop()

        assert dispatcher._stopped is True

    @pytest.mark.asyncio
    async def test_stop_waits_for_running_tasks(self, bot_config, sample_update):
        """Test stop waits for running tasks to complete"""
        config = dataclasses.replace(bot_config, concurrency=2, queue_maxsize=10)
        dispatcher = Dispatcher(config)

        running = False

        class SlowHandler(Handler):
            def check(self, update):  # noqa: ARG002
                return True

            async def handle(self, update):  # noqa: ARG002
                nonlocal running
                running = True
                await asyncio.sleep(0.2)
                running = False

        dispatcher.handlers = [SlowHandler()]

        # Feed update and start dispatcher
        await dispatcher.feed_update(sample_update)
        run_task = asyncio.create_task(dispatcher.run())

        # Wait for handler to start
        await asyncio.sleep(0.05)
        assert running is True

        # Stop dispatcher (should wait for handler)
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        # Handler should have completed
        assert running is False
        assert run_task.done()

    @pytest.mark.asyncio
    async def test_stop_signals_shutdown(self, bot_config):
        """Test stop signals shutdown event"""
        dispatcher = Dispatcher(bot_config)

        async def wait_for_shutdown():
            await dispatcher._shutdown_event.wait()
            return "shutdown received"

        task = asyncio.create_task(wait_for_shutdown())
        await asyncio.sleep(0.05)

        await dispatcher.stop()
        result = await asyncio.wait_for(task, timeout=1.0)

        assert result == "shutdown received"

    @pytest.mark.asyncio
    async def test_stop_can_be_called_multiple_times(self, bot_config):
        """Test stop can be called multiple times without error"""
        dispatcher = Dispatcher(bot_config)

        await dispatcher.stop()
        await dispatcher.stop()  # Should not raise
        await dispatcher.stop()  # Should not raise

        assert dispatcher._stopped is True


class TestDispatcherRun:
    """Tests for run method"""

    @pytest.mark.asyncio
    async def test_run_creates_worker_tasks(self, bot_config):
        """Test run creates worker tasks"""
        config = dataclasses.replace(bot_config, concurrency=3)
        dispatcher = Dispatcher(config)

        run_task = asyncio.create_task(dispatcher.run())
        await asyncio.sleep(0.05)

        # Dispatcher should be running
        assert not run_task.done()

        # Signal shutdown
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        assert run_task.done()

    @pytest.mark.asyncio
    async def test_run_processes_updates(self, bot_config, sample_update):
        """Test run processes updates"""
        config = dataclasses.replace(bot_config, concurrency=1)
        dispatcher = Dispatcher(config)

        handler = MockHandler(should_match=True)
        dispatcher.handlers = [handler]

        # Feed update
        await dispatcher.feed_update(sample_update)

        # Run dispatcher
        run_task = asyncio.create_task(dispatcher.run())
        await asyncio.sleep(0.1)

        # Stop
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        assert len(handler.calls) == 1

    @pytest.mark.asyncio
    async def test_run_cannot_start_stopped_dispatcher(self, bot_config):
        """Test run raises error when called on stopped dispatcher"""
        dispatcher = Dispatcher(bot_config)
        await dispatcher.stop()

        with pytest.raises(RuntimeError, match="Cannot start stopped dispatcher"):
            await dispatcher.run()


class TestDispatcherIntegration:
    """Integration tests for Dispatcher"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, bot_config, sample_update):
        """Test full dispatcher workflow"""
        dispatcher = Dispatcher(bot_config)

        handler = MockHandler(should_match=True)
        dispatcher.register_handler(handler)

        # Feed updates
        for _i in range(5):
            await dispatcher.feed_update(sample_update)

        # Run dispatcher
        run_task = asyncio.create_task(dispatcher.run())
        await asyncio.sleep(0.2)

        # Stop
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        # All updates should be processed
        assert len(handler.calls) == 5

    @pytest.mark.asyncio
    async def test_multiple_handlers_different_filters(self, bot_config, sample_update):
        """Test dispatcher with multiple handlers with different filters"""
        dispatcher = Dispatcher(bot_config)

        handler1 = MockHandler(should_match=True)
        handler2 = MockHandler(should_match=False)

        dispatcher.register_handler(handler1)
        dispatcher.register_handler(handler2)

        # Feed update
        await dispatcher.feed_update(sample_update)

        # Run
        run_task = asyncio.create_task(dispatcher.run())
        await asyncio.sleep(0.1)

        # Stop
        await dispatcher.stop()
        await asyncio.wait_for(run_task, timeout=1.0)

        # Only handler1 should have been called
        assert len(handler1.calls) == 1
        assert len(handler2.calls) == 0
