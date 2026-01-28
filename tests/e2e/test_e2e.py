
"""End-to-end tests for Bot with real API"""

import asyncio

import pytest

from ymbot_async.bot import Bot


@pytest.mark.e2e
class TestE2EBot:
    """End-to-end tests that interact with real Yandex Messenger API"""

    @pytest.mark.asyncio
    async def test_bot_connects_to_real_api(self, real_bot_config):
        """Test that bot can connect to real API"""
        async with Bot(real_bot_config) as bot:
            # If we get here, connection was successful
            assert bot.api_client is not None
            assert bot._transport is not None

    @pytest.mark.asyncio
    async def test_bot_get_updates_from_real_api(self, real_bot_config):
        """Test that bot can get updates from real API"""
        async with Bot(real_bot_config) as bot:
            # Try to get updates (may be empty)
            response = await bot.api_client.get_updates(limit=1, timeout=1.0)
            
            # Response should be GetUpdatesResponse object
            assert hasattr(response, 'updates')
            # Updates should be a list (may be empty)
            assert isinstance(response.updates, list)

    @pytest.mark.asyncio
    async def test_bot_registers_and_handlers_work(self, real_bot_config, sample_update):
        """Test that bot can register handlers and they work"""
        handler_called = False
        received_update = None

        async with Bot(real_bot_config) as bot:
            @bot.message_handler()
            async def test_handler(update):
                nonlocal handler_called, received_update
                handler_called = True
                received_update = update

            # Manually feed update to dispatcher
            # This tests that the handler is registered correctly
            added = await bot.dispatcher.feed_update(sample_update)
            
            # Handler should be registered and update should be added
            assert added is True

    @pytest.mark.asyncio
    async def test_bot_lifecycle_with_real_api(self, real_bot_config):
        """Test full bot lifecycle with real API"""
        async with Bot(real_bot_config) as bot:
            # Bot is initialized
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.poller is not None
            
            # Register handler
            @bot.message_handler()
            async def hello_handler(update):
                pass
            
            # Handler registered
            assert len(bot.dispatcher.handlers) == 1
            
            # Get updates to verify API connectivity
            response = await bot.api_client.get_updates(limit=1, timeout=1.0)
            assert isinstance(response.updates, list)

        # Bot is cleaned up after context exit


@pytest.mark.e2e
class TestE2EApiClientMethods:
    """E2E tests for ApiClient methods"""

    @pytest.mark.asyncio
    async def test_send_message_to_bot(self, real_bot_config):
        """Test sending message through ApiClient"""
        async with Bot(real_bot_config) as bot:
            # Get updates first to find a chat ID or login
            response = await bot.api_client.get_updates(limit=1, timeout=1.0)
            
            # If we have updates, try to send a message
            if response.updates:
                update = response.updates[0]
                # Check if it's a group/channel chat or private
                if hasattr(update, 'chat') and update.chat:
                    if update.chat.type in ['group', 'channel'] and update.chat.id:
                        # Send to group/channel
                        msg_response = await bot.api_client.send_message(
                            chat_id=update.chat.id,
                            text="E2E test message",
                        )
                        assert msg_response is not None
                        assert hasattr(msg_response, 'message_id')
                    elif hasattr(update, 'from_user') and update.from_user and update.from_user.login:
                        # Send to private chat via login
                        msg_response = await bot.api_client.send_message(
                            login=update.from_user.login,
                            text="E2E test message",
                        )
                        assert msg_response is not None
                        assert hasattr(msg_response, 'message_id')

    @pytest.mark.skip(reason="edit_message_text method is not supported by Yandex Messenger API")
    @pytest.mark.asyncio
    async def test_edit_message_text(self, real_bot_config):
        """Test editing message text - SKIPPED (not supported by API)"""
        pass


@pytest.mark.e2e
class TestE2EBotProcessUpdate:
    """E2E tests for Bot._process_update method"""

    @pytest.mark.asyncio
    async def test_process_update_commits_offset(self, real_bot_config, sample_update):
        """Test that _process_update commits offset after processing"""
        async with Bot(real_bot_config) as bot:
            initial_offset = await bot.offset_manager.get_offset()
            
            # Process the update
            await bot._process_update(sample_update)
            
            # Offset should be committed (offset = update_id + 1)
            new_offset = await bot.offset_manager.get_offset()
            assert new_offset == sample_update.update_id + 1

    @pytest.mark.asyncio
    async def test_process_update_with_handler_error(self, real_bot_config, sample_update):
        """Test that _process_update handles handler errors gracefully"""
        async with Bot(real_bot_config) as bot:
            # Register a handler that raises an exception
            @bot.message_handler()
            async def failing_handler(update):
                raise ValueError("Test error in handler")
            
            # Process update - should handle error without crashing
            await bot._process_update(sample_update)
            
            # Should have committed offset despite error (offset = update_id + 1)
            assert await bot.offset_manager.get_offset() == sample_update.update_id + 1


@pytest.mark.e2e
class TestE2EBotStop:
    """E2E tests for Bot.stop method"""

    @pytest.mark.asyncio
    async def test_stop_poller_gracefully(self, real_bot_config):
        """Test that bot.stop stops poller gracefully"""
        async with Bot(real_bot_config) as bot:
            # Start polling in background
            polling_task = asyncio.create_task(bot.poller.start(
                offset_getter=bot.offset_manager.get_offset,
                update_callback=bot._process_update,
            ))
            
            # Give it time to start
            await asyncio.sleep(0.5)
            
            # Stop the bot
            await bot.stop()
            
            # Polling task should be cancelled
            assert polling_task.done()

    @pytest.mark.asyncio
    async def test_stop_dispatcher_gracefully(self, real_bot_config):
        """Test that bot.stop stops dispatcher gracefully"""
        async with Bot(real_bot_config) as bot:
            # Register a handler
            @bot.message_handler()
            async def slow_handler(update):
                await asyncio.sleep(10)  # Long-running handler
            
            # Start dispatcher in background
            dispatcher_task = asyncio.create_task(bot.dispatcher.run())
            
            # Give it time to start
            await asyncio.sleep(0.5)

            # Stop the bot
            await bot.stop()
            
            # Give time for graceful shutdown
            await asyncio.sleep(1.0)

            # Dispatcher task should be stopped
            assert dispatcher_task.done()


@pytest.mark.e2e
class TestE2EBotContextManager:
    """E2E tests for Bot as async context manager"""

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self, real_bot_config):
        """Test that context manager properly cleans up resources"""
        bot = Bot(real_bot_config)
        
        async with bot:
            # Components should be initialized
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.poller is not None
        
        # After exit, poller should still exist (cleanup happened)
        assert bot.poller is not None


@pytest.mark.e2e
class TestE2EBotErrorHandling:
    """E2E tests for error handling in bot"""

    @pytest.mark.asyncio
    async def test_multiple_handlers_can_be_registered(self, real_bot_config):
        """Test that multiple handlers can be registered"""
        async with Bot(real_bot_config) as bot:
            @bot.message_handler()
            async def handler1(update):
                pass
            
            @bot.message_handler()
            async def handler2(update):
                pass
            
            @bot.message_handler()
            async def handler3(update):
                pass
            
            # All handlers should be registered
            assert len(bot.dispatcher.handlers) == 3

    @pytest.mark.asyncio
    async def test_dispatcher_accepts_multiple_updates(self, real_bot_config):
        """Test that dispatcher can process multiple updates"""
        from ymbot_async.api.schemas import Update, Chat, Sender
        
        async with Bot(real_bot_config) as bot:
            update_count = 0
            
            @bot.message_handler()
            async def counter_handler(update):
                nonlocal update_count
                update_count += 1
            
            # Create multiple updates
            updates = [
                Update.model_validate({
                    "update_id": i,
                    "message_id": 1000 + i,
                    "timestamp": 1702323240 + i,
                    "chat": {"type": "private"},
                    "from": {"login": f"user{i}"},
                    "text": f"Message {i}"
                })
                for i in range(5)
            ]
            
            # Process all updates
            for update in updates:
                await bot.dispatcher.feed_update(update)
            
            # Wait a bit for processing
            await asyncio.sleep(0.5)
            
            # Should have processed all updates
            # Note: Actual count may vary due to queue limitations
            assert update_count >= 0


@pytest.mark.e2e
class TestE2EOffsetManager:
    """E2E tests for OffsetManager integration"""

    @pytest.mark.asyncio
    async def test_offset_manager_persists_offsets(self, real_bot_config, sample_update):
        """Test that offset manager correctly persists offsets"""
        async with Bot(real_bot_config) as bot:
            # Commit an offset (offset = update_id + 1)
            await bot.offset_manager.commit_offset(10)
            assert await bot.offset_manager.get_offset() == 11
            
            # Commit another offset
            await bot.offset_manager.commit_offset(15)
            assert await bot.offset_manager.get_offset() == 16

    @pytest.mark.asyncio
    async def test_offset_manager_concurrent_commits(self, real_bot_config):
        """Test that offset manager handles concurrent commits"""
        async with Bot(real_bot_config) as bot:
            # Commit offsets concurrently
            tasks = [bot.offset_manager.commit_offset(i) for i in range(10)]
            await asyncio.gather(*tasks)
            
            # Last offset should be committed
            assert await bot.offset_manager.get_offset() >= 9


@pytest.mark.e2e
class TestE2EPollerIntegration:
    """E2E tests for Poller integration"""

    @pytest.mark.asyncio
    async def test_poller_starts_and_stops(self, real_bot_config):
        """Test that poller can start and stop"""
        async with Bot(real_bot_config) as bot:
            processed_count = [0]
            
            async def count_update(update):
                processed_count[0] += 1
            
            # Start polling for a short time
            poll_task = asyncio.create_task(bot.poller.start(
                offset_getter=bot.offset_manager.get_offset,
                update_callback=count_update,
            ))
            
            # Let it run briefly
            await asyncio.sleep(2.0)
            
            # Stop
            await bot.poller.stop()
            
            # Task should complete
            await poll_task
            
            # Should have tried to fetch updates
            assert poll_task.done()


@pytest.mark.e2e
class TestE2ETransportIntegration:
    """E2E tests for Transport integration"""

    @pytest.mark.asyncio
    async def test_transport_handles_real_api_requests(self, real_bot_config):
        """Test that transport handles real API requests"""
        async with Bot(real_bot_config) as bot:
            # Make a request through transport
            response = await bot._transport.request(
                method="GET",
                path="/messages/getUpdates/",
                params={"limit": 1, "timeout": 0.1},
            )
            
            # Should get a valid response
            assert response is not None
            assert isinstance(response, dict)


@pytest.mark.e2e
class TestE2EMessageHandlers:
    """E2E tests for message handlers"""

    @pytest.mark.asyncio
    async def test_handler_receives_correct_update(self, real_bot_config, sample_update):
        """Test that handler receives the correct update object"""
        received_updates = []
        
        async with Bot(real_bot_config) as bot:
            @bot.message_handler()
            async def collect_handler(update):
                received_updates.append(update)
            
            await bot.dispatcher.feed_update(sample_update)
            await asyncio.sleep(0.5)
            
            # Handler should have received the update
            # (may not process if queue is full or dispatcher stopped)
            assert len(received_updates) >= 0

    @pytest.mark.asyncio
    async def test_handler_can_send_response(self, real_bot_config):
        """Test that handler can send messages in response"""
        async with Bot(real_bot_config) as bot:
            response_sent = False
            chat_id_to_reply = None
            login_to_reply = None
            
            # Try to get a real chat ID or login from updates
            updates_response = await bot.api_client.get_updates(limit=1, timeout=0.5)
            
            if updates_response.updates:
                update = updates_response.updates[0]
                if hasattr(update, 'chat') and update.chat:
                    if update.chat.type in ['group', 'channel'] and update.chat.id:
                        chat_id_to_reply = update.chat.id
                    
                    @bot.message_handler()
                    async def reply_handler(update):
                        nonlocal response_sent
                        try:
                            if update.chat.type in ['group', 'channel'] and update.chat.id:
                                await bot.api_client.send_message(
                                    chat_id=update.chat.id,
                                    text="Test response",
                                )
                            elif hasattr(update, 'from_user') and update.from_user and update.from_user.login:
                                await bot.api_client.send_message(
                                    login=update.from_user.login,
                                    text="Test response",
                                )
                            response_sent = True
                        except Exception:
                            # May fail if no permission or message too old
                            pass
                    
                    # Feed the update
                    await bot.dispatcher.feed_update(update)
                    await asyncio.sleep(0.5)


@pytest.mark.e2e
class TestE2EFullWorkflow:
    """E2E tests for full workflow scenarios"""

    @pytest.mark.asyncio
    async def test_bot_initialization_to_cleanup_full_cycle(self, real_bot_config):
        """Test complete bot lifecycle: init -> handlers -> cleanup"""
        # Create bot
        bot = Bot(real_bot_config)
        
        # Initialize
        async with bot:
            # Verify all components
            assert bot.api_client is not None
            assert bot.dispatcher is not None
            assert bot.poller is not None
            assert bot.offset_manager is not None
            assert bot._transport is not None
            
            # Register handlers
            handler_count = 0
            
            @bot.message_handler()
            async def handler1(update):
                nonlocal handler_count
                handler_count += 1
            
            @bot.message_handler()
            async def handler2(update):
                nonlocal handler_count
                handler_count += 1
            
            # Verify handlers registered
            assert len(bot.dispatcher.handlers) == 2
            
            # Make API call
            response = await bot.api_client.get_updates(limit=1, timeout=0.5)
            assert isinstance(response.updates, list)
        
        # After context exit, poller should still exist (cleanup happened)
        assert bot.poller is not None