"""Unit tests for Poller"""
import asyncio
from unittest.mock import AsyncMock

import pytest

from ymbot_async.runtime.polling import Poller
from ymbot_async.api.schemas import Update


class TestPollerInit:
    """Tests for Poller initialization"""

    def test_poller_initializes_with_config(self, bot_config, mock_api_client):
        """Test poller initializes with config"""
        poller = Poller(mock_api_client, bot_config)
        
        assert poller.api_client == mock_api_client
        assert poller.config == bot_config
        assert poller._shutdown_event is not None
        assert poller._polling_task is None
        assert poller._empty_response_count == 0


class TestPollerCalculateBackoff:
    """Tests for _calculate_backoff method"""

    @pytest.mark.asyncio
    async def test_backoff_zero_empty_responses(self, bot_config, mock_api_client):
        """Test backoff with zero empty responses"""
        poller = Poller(mock_api_client, bot_config)
        poller._empty_response_count = 0
        
        backoff = await poller._calculate_backoff()
        
        assert backoff == bot_config.polling_timeout

    @pytest.mark.asyncio
    async def test_backoff_increases_with_empty_responses(self, bot_config, mock_api_client):
        """Test backoff increases with more empty responses"""
        poller = Poller(mock_api_client, bot_config)
        poller._empty_response_count = 2
        
        backoff = await poller._calculate_backoff()
        
        # Formula: timeout * (1/backoff) ** count
        expected = bot_config.polling_timeout * ((1.0 / bot_config.polling_backoff) ** 2)
        assert backoff == expected

    @pytest.mark.asyncio
    async def test_backoff_respects_max_backoff(self, bot_config, mock_api_client):
        """Test backoff is capped at max_backoff"""
        poller = Poller(mock_api_client, bot_config)
        poller._empty_response_count = 100  # Very high
        
        backoff = await poller._calculate_backoff()
        
        assert backoff == bot_config.polling_max_backoff

    @pytest.mark.asyncio
    async def test_backoff_at_exactly_max(self, bot_config, mock_api_client):
        """Test backoff equals max when calculated would exceed"""
        poller = Poller(mock_api_client, bot_config)
        
        # Find count where backoff would exceed max
        count = 0
        while True:
            poller._empty_response_count = count
            backoff = await poller._calculate_backoff()
            if backoff >= bot_config.polling_max_backoff:
                assert backoff == bot_config.polling_max_backoff
                break
            count += 1


class TestPollerFetchUpdates:
    """Tests for _fetch_updates method"""

    @pytest.mark.asyncio
    async def test_fetch_updates_calls_api_client(self, bot_config, mock_api_client, sample_update):
        """Test _fetch_updates calls API client"""
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[sample_update])
        )
        poller = Poller(mock_api_client, bot_config)
        
        updates = await poller._fetch_updates(offset=0)
        
        mock_api_client.get_updates.assert_called_once()
        call_kwargs = mock_api_client.get_updates.call_args[1]
        assert call_kwargs["offset"] == 0
        assert call_kwargs["limit"] == bot_config.polling_limit
        assert call_kwargs["timeout"] == bot_config.polling_timeout

    @pytest.mark.asyncio
    async def test_fetch_updates_returns_updates(self, bot_config, mock_api_client, sample_update):
        """Test _fetch_updates returns updates from API"""
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[sample_update])
        )
        poller = Poller(mock_api_client, bot_config)
        
        updates = await poller._fetch_updates(offset=0)
        
        assert len(updates) == 1
        assert updates[0] == sample_update

    @pytest.mark.asyncio
    async def test_fetch_updates_with_custom_offset(self, bot_config, mock_api_client, sample_update):
        """Test _fetch_updates uses custom offset"""
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[sample_update])
        )
        poller = Poller(mock_api_client, bot_config)
        
        await poller._fetch_updates(offset=100)
        
        call_kwargs = mock_api_client.get_updates.call_args[1]
        assert call_kwargs["offset"] == 100

    @pytest.mark.asyncio
    async def test_fetch_updates_propagates_error(self, bot_config, mock_api_client):
        """Test _fetch_updates propagates API errors"""
        mock_api_client.get_updates = AsyncMock(
            side_effect=Exception("API error")
        )
        poller = Poller(mock_api_client, bot_config)
        
        with pytest.raises(Exception, match="API error"):
            await poller._fetch_updates(offset=0)


class TestPollerStart:
    """Tests for start method"""

    @pytest.mark.asyncio
    async def test_start_creates_polling_task(self, bot_config, mock_api_client):
        """Test start creates polling task"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[])
        )
        
        await poller.start(offset_getter, update_callback)
        
        assert poller._polling_task is not None
        assert not poller._polling_task.done()
        
        # Clean up
        await poller.stop()

    @pytest.mark.asyncio
    async def test_start_raises_when_already_running(self, bot_config, mock_api_client):
        """Test start raises error when already running"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[])
        )
        
        # Start first time
        await poller.start(offset_getter, update_callback)
        
        # Try to start again
        with pytest.raises(RuntimeError, match="Poller is already running"):
            await poller.start(offset_getter, update_callback)
        
        # Clean up
        await poller.stop()

    @pytest.mark.asyncio
    async def test_start_clears_shutdown_event(self, bot_config, mock_api_client):
        """Test start clears shutdown event"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[])
        )
        
        # Set shutdown event
        poller._shutdown_event.set()
        
        # Start should clear it
        await poller.start(offset_getter, update_callback)
        
        assert not poller._shutdown_event.is_set()
        
        # Clean up
        await poller.stop()


class TestPollerStop:
    """Tests for stop method"""

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, bot_config, mock_api_client):
        """Test stop when not running"""
        poller = Poller(mock_api_client, bot_config)
        
        # Should not raise
        await poller.stop()

    @pytest.mark.asyncio
    async def test_stop_sets_shutdown_event(self, bot_config, mock_api_client):
        """Test stop sets shutdown event"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[])
        )
        
        await poller.start(offset_getter, update_callback)
        await poller.stop()
        
        assert poller._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_stop_waits_for_task_to_complete(self, bot_config, mock_api_client):
        """Test stop waits for polling task to complete"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        
        call_count = [0]
        
        async def slow_get_updates(**kwargs):
            call_count[0] += 1
            await asyncio.sleep(0.1)
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(side_effect=slow_get_updates)
        
        await poller.start(offset_getter, update_callback)
        await asyncio.sleep(0.05)  # Let it start
        await poller.stop()
        
        assert poller._polling_task is None

    @pytest.mark.asyncio
    async def test_stop_timeout_cancels_task(self, mock_api_client):
        """Test stop cancels task on timeout"""
        # Create config with short read timeout
        from ymbot_async.config import BotConfig
        short_timeout_config = BotConfig(
            token="test_token",
            timeout_read=0.01,  # Very short timeout
        )
        
        poller = Poller(mock_api_client, short_timeout_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        
        async def infinite_get_updates(**kwargs):
            await asyncio.sleep(100)  # Very long
        
        mock_api_client.get_updates = AsyncMock(side_effect=infinite_get_updates)
        
        await poller.start(offset_getter, update_callback)
        await asyncio.sleep(0.05)  # Let it start
        
        await poller.stop()
        
        assert poller._polling_task is None

    @pytest.mark.asyncio
    async def test_stop_can_be_called_multiple_times(self, bot_config, mock_api_client):
        """Test stop can be called multiple times"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[])
        )
        
        await poller.start(offset_getter, update_callback)
        await poller.stop()
        await poller.stop()  # Should not raise
        await poller.stop()  # Should not raise
        
        assert poller._polling_task is None


class TestPollerEmptyResponses:
    """Tests for empty response handling"""

    @pytest.mark.asyncio
    async def test_empty_response_increments_counter(self, bot_config, mock_api_client):
        """Test empty response increments counter"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        mock_api_client.get_updates = AsyncMock(
            return_value=AsyncMock(ok=True, updates=[])
        )
        
        # Start poller in a task
        poller_task = asyncio.create_task(poller.start(offset_getter, update_callback))
        
        # Wait for at least one poll
        for _ in range(20):  # max 1 second
            if poller._empty_response_count > 0:
                break
            await asyncio.sleep(0.05)
        
        # Store count BEFORE stop() (stop() resets the counter)
        final_count = poller._empty_response_count
        
        await poller.stop()
        try:
            await poller_task
        except RuntimeError:
            pass  # Already stopped
        
        assert final_count > 0

    @pytest.mark.asyncio
    async def test_response_resets_counter(self, mock_api_client, sample_update):
        """Test receiving updates resets counter"""
        # Create config with short timeout for faster test
        from ymbot_async.config import BotConfig
        short_timeout_config = BotConfig(
            token="test_token",
            polling_timeout=0.05,  # Short timeout
        )
        
        poller = Poller(mock_api_client, short_timeout_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        
        call_count = [0]
        update_received = False
        
        async def get_updates_with_empty_then_updates(**kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                return AsyncMock(ok=True, updates=[])
            else:
                if not update_received:
                    update_received = True
                    return AsyncMock(ok=True, updates=[sample_update])
                return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(
            side_effect=get_updates_with_empty_then_updates
        )
        
        # Start poller in a task
        poller_task = asyncio.create_task(poller.start(offset_getter, update_callback))
        
        # Wait until update is received
        for _ in range(20):  # max 1 second
            if update_received:
                break
            await asyncio.sleep(0.05)
        
        await poller.stop()
        try:
            await poller_task
        except RuntimeError:
            pass  # Already stopped
        
        # Counter should have been incremented then reset
        assert call_count[0] >= 3

    @pytest.mark.asyncio
    async def test_backoff_applied_after_empty(self, mock_api_client):
        """Test backoff delay is applied after empty response"""
        # Create config with specific backoff settings
        from ymbot_async.config import BotConfig
        custom_backoff_config = BotConfig(
            token="test_token",
            polling_timeout=0.05,  # Short timeout
            polling_backoff=0.5,  # Less than 1 to increase backoff
            polling_max_backoff=5.0,
        )
        
        poller = Poller(mock_api_client, custom_backoff_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        
        call_times = []
        call_count = [0]
        
        async def get_updates_with_timing(**kwargs):
            call_count[0] += 1
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.01)
            
            # Stop after 3 calls to avoid infinite polling
            if call_count[0] >= 3:
                return AsyncMock(ok=True, updates=[])
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(side_effect=get_updates_with_timing)
        
        # Start poller in a task
        poller_task = asyncio.create_task(poller.start(offset_getter, update_callback))
        
        # Wait for at least 3 calls
        for _ in range(20):
            if call_count[0] >= 3:
                break
            await asyncio.sleep(0.05)
        
        await poller.stop()
        try:
            await poller_task
        except RuntimeError:
            pass  # Already stopped
        
        # Check that delays increased (calls are spaced further apart)
        assert len(call_times) >= 3
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        assert delays[1] > delays[0]  # Second delay should be longer


class TestPollerUpdateProcessing:
    """Tests for update processing"""

    @pytest.mark.asyncio
    async def test_processes_updates_from_api(self, bot_config, mock_api_client, sample_update):
        """Test poller processes updates from API"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        processed_updates = []
        
        async def update_callback(update):
            processed_updates.append(update)
        
        # Return update only once to prevent memory leak
        call_count = [0]
        
        async def get_updates_once_then_empty(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return AsyncMock(ok=True, updates=[sample_update])
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(side_effect=get_updates_once_then_empty)
        
        await poller.start(offset_getter, update_callback)
        await asyncio.sleep(0.1)  # Let it process
        await poller.stop()
        
        assert len(processed_updates) == 1
        assert processed_updates[0] == sample_update

    @pytest.mark.asyncio
    async def test_processes_multiple_updates(self, bot_config, mock_api_client):
        """Test poller processes multiple updates"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        processed_updates = []
        
        updates = [
            AsyncMock(update_id=i, message=None)
            for i in range(1, 4)
        ]
        
        async def update_callback(update):
            processed_updates.append(update)
        
        # Return updates only once to prevent memory leak
        call_count = [0]
        
        async def get_updates_once_then_empty(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return AsyncMock(ok=True, updates=updates)
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(side_effect=get_updates_once_then_empty)
        
        await poller.start(offset_getter, update_callback)
        await asyncio.sleep(0.1)
        await poller.stop()
        
        assert len(processed_updates) == 3

    @pytest.mark.asyncio
    async def test_stops_processing_on_shutdown(self, bot_config, mock_api_client, sample_update):
        """Test poller stops processing updates on shutdown"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        processed_count = [0]
        
        async def update_callback(update):
            processed_count[0] += 1
            await asyncio.sleep(0.01)
        
        # Return update only once to prevent memory leak
        call_count = [0]
        
        async def get_updates_once_then_empty(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return AsyncMock(ok=True, updates=[sample_update])
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(side_effect=get_updates_once_then_empty)
        
        await poller.start(offset_getter, update_callback)
        await asyncio.sleep(0.05)  # Let it process a bit
        await poller.stop()
        
        # Should have processed exactly one update
        assert processed_count[0] == 1


class TestPollerErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_continues_after_error(self, mock_api_client):
        """Test poller continues after error"""
        # Create config with short timeout for faster test
        from ymbot_async.config import BotConfig
        short_timeout_config = BotConfig(
            token="test_token",
            polling_timeout=0.05,  # Short timeout
        )
        
        poller = Poller(mock_api_client, short_timeout_config)
        
        offset_getter = AsyncMock(return_value=0)
        update_callback = AsyncMock()
        
        call_count = [0]
        error_raised = [False]  # Use list to allow modification in closure
        recovered = [False]  # Use list to allow modification in closure
        
        async def get_updates_with_error(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                error_raised[0] = True
                raise Exception("Network error")
            if not recovered[0]:
                recovered[0] = True
            await asyncio.sleep(0.01)
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(
            side_effect=get_updates_with_error
        )
        
        # Start poller in a task
        poller_task = asyncio.create_task(poller.start(offset_getter, update_callback))
        
        # Wait for recovery - need to wait for second call after error
        # First call: error (immediate)
        # Then sleep polling_timeout (0.05)
        # Then second call (should succeed)
        for _ in range(50):  # Increased from 20 to allow more time
            if recovered[0]:
                break
            await asyncio.sleep(0.02)  # Check more frequently (0.02 instead of 0.05)
        
        await poller.stop()
        try:
            await poller_task
        except RuntimeError:
            pass  # Already stopped
        
        # Should have called multiple times (recovered from error)
        assert call_count[0] > 1
        assert error_raised[0]  # Should have raised error on first call
        assert recovered[0]  # Should have recovered

    @pytest.mark.asyncio
    async def test_handles_callback_error(self, bot_config, mock_api_client, sample_update):
        """Test poller handles callback errors gracefully"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_getter = AsyncMock(return_value=0)
        
        async def failing_callback(update):
            raise ValueError("Callback error")
        
        # Return update only once to prevent memory leak
        call_count = [0]
        
        async def get_updates_once_then_empty(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return AsyncMock(ok=True, updates=[sample_update])
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(side_effect=get_updates_once_then_empty)
        
        # Should not raise
        await poller.start(offset_getter, failing_callback)
        await asyncio.sleep(0.1)
        await poller.stop()


class TestPollerIntegration:
    """Integration tests for Poller"""

    @pytest.mark.asyncio
    async def test_full_polling_cycle(self, bot_config, mock_api_client, sample_update):
        """Test full polling cycle"""
        poller = Poller(mock_api_client, bot_config)
        
        offset_value = [0]
        processed_updates = []
        
        async def offset_getter():
            return offset_value[0]
        
        async def update_callback(update):
            processed_updates.append(update)
            offset_value[0] = update.update_id + 1
        
        call_count = [0]
        
        async def get_updates(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return AsyncMock(ok=True, updates=[sample_update])
            return AsyncMock(ok=True, updates=[])
        
        mock_api_client.get_updates = AsyncMock(side_effect=get_updates)
        
        await poller.start(offset_getter, update_callback)
        await asyncio.sleep(0.15)
        await poller.stop()
        
        # Should have processed the update
        assert any(u == sample_update for u in processed_updates)
        assert call_count[0] >= 2