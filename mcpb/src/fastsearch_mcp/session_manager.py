"""Session management for FastSearch MCP server."""

import asyncio
import logging
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions for the MCP server."""

    def __init__(self, session_timeout: int = 3600):
        """Initialize the session manager.

        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.sessions: dict[str, dict[str, Any]] = {}
        self.session_timeout = session_timeout
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the session cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_sessions())

    async def stop(self) -> None:
        """Stop the session cleanup task."""
        self._running = False
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def get_or_create_session(self, session_id: str | None = None) -> tuple[str, dict[str, Any]]:
        """Get an existing session or create a new one.

        Args:
            session_id: Optional session ID to look up

        Returns:
            A tuple of (session_id, session_data)
        """
        now = time.time()

        if session_id and session_id in self.sessions:
            # Update last activity for existing session
            self.sessions[session_id]["last_activity"] = now
            return session_id, self.sessions[session_id]

        # Create new session
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {"created_at": now, "last_activity": now, "data": {}}
        return session_id, self.sessions[session_id]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get a session by ID if it exists and is not expired.

        Args:
            session_id: The session ID to look up

        Returns:
            The session data if found and not expired, None otherwise
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        now = time.time()

        # Check if session has expired
        if now - session["last_activity"] > self.session_timeout:
            del self.sessions[session_id]
            return None

        # Update last activity
        session["last_activity"] = now
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: The session ID to delete

        Returns:
            True if the session was deleted, False if it didn't exist
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def _cleanup_sessions(self) -> None:
        """Background task to clean up expired sessions."""
        while self._running:
            try:
                now = time.time()
                expired = [
                    sid
                    for sid, session in self.sessions.items()
                    if now - session["last_activity"] > self.session_timeout
                ]

                for sid in expired:
                    logger.debug("Cleaning up expired session: %s", sid)
                    del self.sessions[sid]

            except Exception as e:
                logger.error("Error cleaning up sessions: %s", e, exc_info=True)

            # Wait before checking again
            await asyncio.sleep(300)  # Check every 5 minutes
