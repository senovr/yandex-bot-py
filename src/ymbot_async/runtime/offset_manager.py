"""
Offset management for long polling
"""

import asyncio
from typing import Any

from ymbot_async.api.schemas import Update
from ymbot_async.config import BotConfig
from ymbot_async.errors import OffsetError
from ymbot_async.logging import get_logger, LoggerProtocol

logger: LoggerProtocol = get_logger(__name__)


class OffsetManager:
    """
    Thread-safe offset manager for long polling.
    
    Features:
    - Save offset only after handler completes successfully
    - Prevent offset regressions
    - Thread-safe operations
    """

    def __init__(
        self,
        config: BotConfig,
        initial_offset: int = 0,
    ):
        """
        Initialize offset manager.
        
        Args:
            config: Bot configuration
            initial_offset: Initial offset value
        """
        self.config = config
        self._current_offset = initial_offset
        self._offset_lock = asyncio.Lock()

        logger.info(
            "Offset manager initialized",
            initial_offset=initial_offset,
        )

    async def get_offset(self) -> int:
        """
        Get current offset.
        
        Returns:
            Current offset value
        """
        async with self._offset_lock:
            return self._current_offset

    async def commit_offset(self, update_id: int) -> None:
        """
        Commit offset after successful update processing.
        
        Args:
            update_id: Update ID to commit
            
        Raises:
            OffsetError: If offset would regress (strict regression)
        """
        async with self._offset_lock:
            # Calculate new offset
            new_offset = update_id + 1
            
            # Prevent strict regression (going backwards)
            # Allow same offset (already committed by concurrent task)
            if new_offset < self._current_offset:
                logger.warning(
                    "Attempted to regress offset",
                    update_id=update_id,
                    current_offset=self._current_offset,
                    new_offset=new_offset,
                )
                raise OffsetError(
                    f"Cannot regress offset from {self._current_offset} to {new_offset}"
                )
            
            # Skip if already committed (concurrent task committed same offset)
            if new_offset <= self._current_offset:
                return

            # Update offset
            logger.debug(
                "Committed offset",
                old_offset=self._current_offset,
                new_offset=new_offset,
                update_id=update_id,
            )
            self._current_offset = new_offset

    async def save_offset_to_storage(self) -> dict[str, Any]:
        """
        Save offset to storage.
        
        This is a placeholder for persistent storage (database, file, etc.).
        Override this method to implement custom storage.
        
        Returns:
            Storage response
        """
        # TODO: Implement persistent storage
        async with self._offset_lock:
            logger.info(
                "Saving offset to storage",
                offset=self._current_offset,
            )
            return {"offset": self._current_offset, "saved": True}

    async def load_offset_from_storage(self) -> int:
        """
        Load offset from storage.
        
        This is a placeholder for persistent storage (database, file, etc.).
        Override this method to implement custom storage.
        
        Returns:
            Loaded offset value
        """
        # TODO: Implement persistent storage
        logger.info("Loading offset from storage")
        return self._current_offset