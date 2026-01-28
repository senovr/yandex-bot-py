"""Unit tests for OffsetManager"""
import asyncio

import pytest

from ymbot_async.runtime.offset_manager import OffsetManager
from ymbot_async.errors import OffsetError


class TestOffsetManagerInit:
    """Tests for OffsetManager initialization"""

    def test_offset_manager_initializes_with_default_offset(self, bot_config):
        """Test offset manager initializes with default offset 0"""
        manager = OffsetManager(bot_config)
        
        assert manager._current_offset == 0

    def test_offset_manager_initializes_with_custom_offset(self, bot_config):
        """Test offset manager initializes with custom offset"""
        manager = OffsetManager(bot_config, initial_offset=100)
        
        assert manager._current_offset == 100

    def test_offset_manager_has_lock(self, bot_config):
        """Test offset manager has asyncio lock"""
        manager = OffsetManager(bot_config)
        
        assert isinstance(manager._offset_lock, asyncio.Lock)


class TestOffsetManagerGetOffset:
    """Tests for get_offset method"""

    @pytest.mark.asyncio
    async def test_get_offset_returns_initial(self, bot_config):
        """Test get_offset returns initial offset"""
        manager = OffsetManager(bot_config, initial_offset=50)
        
        offset = await manager.get_offset()
        
        assert offset == 50

    @pytest.mark.asyncio
    async def test_get_offset_after_commit(self, bot_config):
        """Test get_offset returns offset after commit"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        await manager.commit_offset(10)
        offset = await manager.get_offset()
        
        assert offset == 11  # update_id + 1

    @pytest.mark.asyncio
    async def test_get_offset_is_thread_safe(self, bot_config):
        """Test get_offset is thread-safe with concurrent access"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Simulate concurrent access
        tasks = [manager.get_offset() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should return the same value
        assert all(r == 0 for r in results)


class TestOffsetManagerCommitOffset:
    """Tests for commit_offset method"""

    @pytest.mark.asyncio
    async def test_commit_offset_increments_by_one(self, bot_config):
        """Test commit_offset sets offset to update_id + 1"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        await manager.commit_offset(10)
        
        offset = await manager.get_offset()
        assert offset == 11

    @pytest.mark.asyncio
    async def test_commit_multiple_offsets(self, bot_config):
        """Test committing multiple offsets sequentially"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        await manager.commit_offset(10)
        assert await manager.get_offset() == 11
        
        await manager.commit_offset(20)
        assert await manager.get_offset() == 21
        
        await manager.commit_offset(30)
        assert await manager.get_offset() == 31

    @pytest.mark.asyncio
    async def test_commit_offset_raises_on_regression(self, bot_config):
        """Test commit_offset raises error on offset regression"""
        manager = OffsetManager(bot_config, initial_offset=20)
        
        with pytest.raises(OffsetError) as exc_info:
            await manager.commit_offset(10)
        
        assert "Cannot regress offset" in str(exc_info.value)
        assert "20" in str(exc_info.value)
        # The new offset would be 11 (update_id 10 + 1)
        assert "11" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_commit_offset_ignores_equal_offset(self, bot_config):
        """Test commit_offset ignores commit when update_id sets same offset"""
        manager = OffsetManager(bot_config, initial_offset=10)
        
        # Would set offset to 10, equal to current - should be ignored, not raise
        await manager.commit_offset(9)
        
        # Offset should still be 10 (unchanged)
        offset = await manager.get_offset()
        assert offset == 10

    @pytest.mark.asyncio
    async def test_commit_offset_is_thread_safe(self, bot_config):
        """Test commit_offset is thread-safe with concurrent access"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Concurrent commits with different values
        tasks = [manager.commit_offset(i * 10) for i in range(1, 11)]
        await asyncio.gather(*tasks)
        
        # Offset should be at least 100 (highest update_id + 1)
        offset = await manager.get_offset()
        assert offset >= 100

    @pytest.mark.asyncio
    async def test_commit_offset_preserves_increasing_sequence(self, bot_config):
        """Test commit_offset maintains increasing sequence"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Commit in increasing order
        for i in range(1, 6):
            await manager.commit_offset(i * 10)
            offset = await manager.get_offset()
            assert offset == i * 10 + 1


class TestOffsetManagerPreventRegression:
    """Tests for offset regression prevention"""

    @pytest.mark.asyncio
    async def test_cannot_commit_lower_offset(self, bot_config):
        """Test cannot commit offset lower than current"""
        manager = OffsetManager(bot_config, initial_offset=100)
        
        with pytest.raises(OffsetError):
            await manager.commit_offset(50)

    @pytest.mark.asyncio
    async def test_commit_equal_offset_is_ignored(self, bot_config):
        """Test commit offset equal to current offset - 1 is ignored"""
        manager = OffsetManager(bot_config, initial_offset=100)
        
        # Current offset is 100, so update_id 99 would set offset to 100
        # Should be ignored, not raise error
        await manager.commit_offset(99)
        
        # Offset should still be 100
        assert await manager.get_offset() == 100

    @pytest.mark.asyncio
    async def test_can_commit_higher_offset(self, bot_config):
        """Test can commit offset higher than current"""
        manager = OffsetManager(bot_config, initial_offset=100)
        
        # Should succeed
        await manager.commit_offset(200)
        assert await manager.get_offset() == 201

    @pytest.mark.asyncio
    async def test_offset_preserved_after_failed_commit(self, bot_config):
        """Test offset remains unchanged after failed commit"""
        manager = OffsetManager(bot_config, initial_offset=50)
        
        # Try to commit lower offset (should fail)
        with pytest.raises(OffsetError):
            await manager.commit_offset(10)
        
        # Offset should still be 50
        assert await manager.get_offset() == 50


class TestOffsetManagerStorage:
    """Tests for storage methods"""

    @pytest.mark.asyncio
    async def test_save_offset_to_storage(self, bot_config):
        """Test save_offset_to_storage returns correct data"""
        manager = OffsetManager(bot_config, initial_offset=100)
        
        result = await manager.save_offset_to_storage()
        
        assert result["offset"] == 100
        assert result["saved"] is True

    @pytest.mark.asyncio
    async def test_save_offset_after_commit(self, bot_config):
        """Test save_offset_to_storage saves committed offset"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        await manager.commit_offset(50)
        result = await manager.save_offset_to_storage()
        
        assert result["offset"] == 51

    @pytest.mark.asyncio
    async def test_load_offset_from_storage(self, bot_config):
        """Test load_offset_from_storage returns current offset"""
        manager = OffsetManager(bot_config, initial_offset=100)
        
        offset = await manager.load_offset_from_storage()
        
        assert offset == 100

    @pytest.mark.asyncio
    async def test_load_offset_after_commit(self, bot_config):
        """Test load_offset_from_storage returns committed offset"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        await manager.commit_offset(50)
        offset = await manager.load_offset_from_storage()
        
        assert offset == 51

    @pytest.mark.asyncio
    async def test_storage_methods_are_thread_safe(self, bot_config):
        """Test storage methods are thread-safe"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Concurrent storage operations
        tasks = [
            manager.save_offset_to_storage(),
            manager.load_offset_from_storage(),
            manager.save_offset_to_storage(),
        ]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r is not None for r in results)


class TestOffsetManagerConcurrency:
    """Tests for concurrent offset operations"""

    @pytest.mark.asyncio
    async def test_concurrent_commits_dont_corrupt_offset(self, bot_config):
        """Test concurrent commits don't corrupt offset state"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Create many concurrent commits
        async def commit_and_get(i):
            await manager.commit_offset(i)
            return await manager.get_offset()
        
        tasks = [commit_and_get(i) for i in range(1, 101)]
        await asyncio.gather(*tasks)
        
        # Final offset should be at least 100
        final_offset = await manager.get_offset()
        assert final_offset >= 100

    @pytest.mark.asyncio
    async def test_concurrent_gets_are_consistent(self, bot_config):
        """Test concurrent gets return consistent values"""
        manager = OffsetManager(bot_config, initial_offset=42)
        
        # Get offset from many tasks
        tasks = [manager.get_offset() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        # All should return the same value
        assert all(r == 42 for r in results)

    @pytest.mark.asyncio
    async def test_interleaved_commits_and_gets(self, bot_config):
        """Test interleaved commits and gets work correctly"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Track offsets per worker
        results = []
        
        async def worker(worker_id):
            # Each worker uses unique update_ids (offset by worker_id * 10)
            base_offset = worker_id * 10
            for i in range(10):
                update_id = base_offset + i
                await manager.commit_offset(update_id)
                offset = await manager.get_offset()
                results.append((worker_id, update_id, offset))
        
        # Run multiple workers
        await asyncio.gather(*[worker(i) for i in range(5)])
        
        # Each commit should result in offset >= update_id + 1
        # Note: In concurrent scenarios, offsets may not be strictly increasing globally
        # but each individual commit should be >= update_id + 1
        for _, update_id, offset in results:
            assert offset >= update_id + 1

    @pytest.mark.asyncio
    async def test_regression_during_concurrent_commits(self, bot_config):
        """Test regression is prevented during concurrent commits"""
        manager = OffsetManager(bot_config, initial_offset=100)
        
        # Try to commit both higher and lower offsets concurrently
        high_task = asyncio.create_task(manager.commit_offset(200))
        low_task = asyncio.create_task(manager.commit_offset(50))
        
        # High should succeed, low should fail
        results = await asyncio.gather(high_task, low_task, return_exceptions=True)
        
        # First should succeed (no exception), second should fail
        assert not isinstance(results[0], Exception)
        assert isinstance(results[1], OffsetError)


class TestOffsetManagerEdgeCases:
    """Tests for edge cases"""

    @pytest.mark.asyncio
    async def test_commit_zero_offset(self, bot_config):
        """Test committing zero offset"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Should succeed (update_id 0 sets offset to 1)
        await manager.commit_offset(0)
        assert await manager.get_offset() == 1

    @pytest.mark.asyncio
    async def test_commit_negative_offset(self, bot_config):
        """Test committing negative offset raises error"""
        manager = OffsetManager(bot_config, initial_offset=10)
        
        with pytest.raises(OffsetError):
            await manager.commit_offset(-1)

    @pytest.mark.asyncio
    async def test_commit_very_large_offset(self, bot_config):
        """Test committing very large offset"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        await manager.commit_offset(10**9)
        assert await manager.get_offset() == 10**9 + 1

    @pytest.mark.asyncio
    async def test_get_offset_without_commits(self, bot_config):
        """Test getting offset without any commits"""
        manager = OffsetManager(bot_config, initial_offset=999)
        
        offset = await manager.get_offset()
        assert offset == 999


class TestOffsetManagerLocking:
    """Tests for locking behavior"""

    @pytest.mark.asyncio
    async def test_get_offset_acquires_lock(self, bot_config):
        """Test get_offset acquires lock"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Acquire lock externally
        async with manager._offset_lock:
            # Try to get offset (should wait for lock to release)
            task = asyncio.create_task(manager.get_offset())
            
            # Check if task is waiting
            await asyncio.sleep(0.01)
            assert not task.done()
        
        # Now task should complete
        result = await asyncio.wait_for(task, timeout=1.0)
        assert result == 0

    @pytest.mark.asyncio
    async def test_commit_offset_acquires_lock(self, bot_config):
        """Test commit_offset acquires lock"""
        manager = OffsetManager(bot_config, initial_offset=0)
        
        # Acquire lock externally
        async with manager._offset_lock:
            # Try to commit offset (should wait)
            task = asyncio.create_task(manager.commit_offset(10))
            
            await asyncio.sleep(0.01)
            assert not task.done()
        
        # Now should complete
        await asyncio.wait_for(task, timeout=1.0)
        assert await manager.get_offset() == 11