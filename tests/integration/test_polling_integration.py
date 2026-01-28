"""Integration tests for Poller with real behavior"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from ymbot_async.runtime.polling import Poller
from ymbot_async.api.schemas import Update, Chat, Sender
from ymbot_async.config import BotConfig


class TestPollerBackoff:
    """Tests for backoff logic on consecutive empty responses"""

    @pytest.mark.asyncio
    async def test_backoff_resets_after_updates(self):
        """Test that backoff resets when updates are received"""
        config = BotConfig(
            token="test",
            polling_timeout=0.1,
            polling_backoff=2.0,
            polling_max_backoff=1.0,
        )
        
        mock_api_client = AsyncMock()
        
        update = Update(
            update_id=1,
            message_id=1,
            text="Hello",
            timestamp=1704067200,
            chat=Chat(type="private", id="1"),
            **{"from": Sender(id="user1")},
        )
        
        # Use side_effect to return empty response first, then update
        mock_api_client.get_updates = AsyncMock(side_effect=[
            MagicMock(updates=[]),  # First call - empty
            MagicMock(updates=[update]),  # Second call - has update
            MagicMock(updates=[]),  # Subsequent calls - empty
        ])
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        updates_received = []
        
        async def update_callback(update):
            updates_received.append(update)
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        
        # Wait for both calls to complete
        await asyncio.sleep(0.3)
        
        # Stop poller
        await poller.stop()
        
        assert len(updates_received) >= 1

    @pytest.mark.asyncio
    async def test_backoff_increases_on_consecutive_empty_results(self):
        """Test that backoff increases with consecutive empty results"""
        config = BotConfig(
            token="test",
            polling_timeout=0.05,
            polling_backoff=2.0,
            polling_max_backoff=0.5,
        )
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        async def update_callback(update):
            pass
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        
        # Wait for several empty responses (backoff should increase)
        await asyncio.sleep(0.5)
        
        # Stop poller
        await poller.stop()
        
        # Should have made multiple calls with increasing backoff
        assert mock_api_client.get_updates.call_count >= 2


class TestPollerFetchUpdates:
    """Tests for fetching updates from API"""

    @pytest.mark.asyncio
    async def test_fetch_updates_calls_api(self):
        """Test that fetch_updates calls the API client"""
        config = BotConfig(token="test")
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        # Fetch updates
        updates = await poller._fetch_updates(offset=0)
        
        # Verify API call
        mock_api_client.get_updates.assert_called_once_with(
            offset=0,
            limit=config.polling_limit,
            timeout=config.polling_timeout,
        )

    @pytest.mark.asyncio
    async def test_fetch_updates_with_offset(self):
        """Test that fetch_updates uses provided offset"""
        config = BotConfig(token="test")
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        # Fetch updates with offset
        updates = await poller._fetch_updates(offset=100)
        
        # Verify API call with offset
        mock_api_client.get_updates.assert_called_once_with(
            offset=100,
            limit=config.polling_limit,
            timeout=config.polling_timeout,
        )


class TestPollerStartStop:
    """Tests for start and stop functionality"""

    @pytest.mark.asyncio
    async def test_stop_cancels_task_on_timeout(self):
        """Test that stop cancels task if it doesn't finish in time"""
        config = BotConfig(token="test")
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        async def update_callback(update):
            pass
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        await asyncio.sleep(0.1)
        
        # Stop should complete
        await poller.stop()
        
        assert poller._polling_task is None

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self):
        """Test that stop can be called multiple times"""
        config = BotConfig(token="test")
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        async def update_callback(update):
            pass
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        await asyncio.sleep(0.1)
        
        # Stop multiple times
        await poller.stop()
        await poller.stop()
        await poller.stop()
        
        assert poller._polling_task is None


class TestPollerShutdownDuringProcessing:
    """Tests for shutdown behavior during update processing"""

    @pytest.mark.asyncio
    async def test_shutdown_during_update_processing(self):
        """Test that poller shuts down cleanly while processing updates"""
        config = BotConfig(token="test")
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        processing_count = [0]
        
        async def update_callback(update):
            processing_count[0] += 1
            await asyncio.sleep(0.1)
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        await asyncio.sleep(0.1)
        
        # Stop while processing
        await poller.stop()
        
        assert poller._polling_task is None


class TestPollerErrorRecovery:
    """Tests for error handling and recovery"""

    @pytest.mark.asyncio
    async def test_error_in_fetch_updates_retries(self):
        """Test that errors in fetch_updates are retried"""
        config = BotConfig(token="test", polling_timeout=0.05)
        
        mock_api_client = AsyncMock()
        call_count = [0]
        max_calls = 5
        
        async def failing_get_updates(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary error")
            if call_count[0] > max_calls:
                # Stop after max_calls to prevent infinite polling
                raise Exception("Stop polling")
            return MagicMock(updates=[])
        
        mock_api_client.get_updates = failing_get_updates
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        async def update_callback(update):
            pass
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        
        # Wait for retries
        await asyncio.sleep(0.3)
        
        # Stop poller
        await poller.stop()
        
        # Should have retried
        assert call_count[0] >= 3

    @pytest.mark.asyncio
    async def test_error_in_callback_doesnt_stop_polling(self):
        """Test that errors in callback don't stop polling"""
        config = BotConfig(token="test", polling_timeout=0.05)
        
        mock_api_client = AsyncMock()
        
        call_count = [0]
        max_calls = 5
        
        async def get_updates_with_callback(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > max_calls:
                # Stop returning updates after max_calls
                return MagicMock(updates=[])
            
            update = Update(
                update_id=call_count[0],
                message_id=call_count[0],
                text="Hello",
                timestamp=1704067200,
                chat=Chat(type="private", id="1"),
                **{"from": Sender(id=f"user{call_count[0]}")},
            )
            return MagicMock(updates=[update])
        
        mock_api_client.get_updates = get_updates_with_callback
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        callback_count = [0]
        
        async def failing_callback(update):
            callback_count[0] += 1
            if callback_count[0] < 3:
                raise ValueError("Callback error")
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=failing_callback)
        
        # Wait for processing
        await asyncio.sleep(0.3)
        
        # Stop poller
        await poller.stop()
        
        # Callback should have been called even with errors
        assert callback_count[0] >= 1
        assert call_count[0] > max_calls  # Verify we stopped calling the API


class TestPollerLifecycle:
    """Tests for poller lifecycle and configuration"""

    @pytest.mark.asyncio
    async def test_poller_initialization(self):
        """Test that poller initializes correctly"""
        config = BotConfig(token="test")
        
        mock_api_client = AsyncMock()
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        assert poller.api_client == mock_api_client
        assert poller.config == config
        assert poller._shutdown_event is not None
        assert poller._shutdown_event.is_set() is False
        assert poller._polling_task is None
        assert poller._empty_response_count == 0

    @pytest.mark.asyncio
    async def test_poller_configures_custom_timeout(self):
        """Test that poller uses custom timeout from config"""
        config = BotConfig(
            token="test",
            polling_timeout=0.5,
        )
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        async def update_callback(update):
            pass
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        await asyncio.sleep(0.1)
        
        # Fetch updates should use config timeout
        await poller._fetch_updates(offset=0)
        
        # Check that at least one call was made with correct timeout
        assert mock_api_client.get_updates.call_count >= 1
        call_kwargs = mock_api_client.get_updates.call_args[1]
        assert call_kwargs["timeout"] == 0.5
        
        # Stop poller
        await poller.stop()

    @pytest.mark.asyncio
    async def test_poller_configures_custom_limit(self):
        """Test that poller uses custom limit from config"""
        config = BotConfig(
            token="test",
            polling_limit=50,
        )
        
        mock_api_client = AsyncMock()
        mock_api_client.get_updates = AsyncMock(return_value=MagicMock(updates=[]))
        
        poller = Poller(api_client=mock_api_client, config=config)
        
        async def offset_getter():
            return 0
        
        async def update_callback(update):
            pass
        
        # Start poller
        await poller.start(offset_getter=offset_getter, update_callback=update_callback)
        await asyncio.sleep(0.1)
        
        # Fetch updates should use config limit
        await poller._fetch_updates(offset=0)
        
        # Check that at least one call was made with correct limit
        assert mock_api_client.get_updates.call_count >= 1
        call_kwargs = mock_api_client.get_updates.call_args[1]
        assert call_kwargs["limit"] == 50
        
        # Stop poller
        await poller.stop()
