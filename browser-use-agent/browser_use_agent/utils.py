"""Utility functions for browser automation agent."""

import hashlib
from typing import Dict, Optional


class StreamManager:
    """Manages WebSocket streaming ports for browser sessions."""
    
    def __init__(self, base_port: int = 9223, max_offset: int = 1000):
        """Initialize stream manager.
        
        Args:
            base_port: Base port number for streaming
            max_offset: Maximum port offset
        """
        self.base_port = base_port
        self.max_offset = max_offset
        self._active_ports: Dict[str, int] = {}
    
    def get_port_for_thread(self, thread_id: str) -> int:
        """Get or allocate a stream port for a thread.
        
        Args:
            thread_id: Unique thread identifier
            
        Returns:
            int: WebSocket port number for this thread
        """
        if thread_id in self._active_ports:
            return self._active_ports[thread_id]
        
        # Calculate port based on thread ID hash
        port_offset = int(hashlib.md5(thread_id.encode()).hexdigest(), 16) % self.max_offset
        port = self.base_port + port_offset
        
        self._active_ports[thread_id] = port
        return port
    
    def get_stream_url(self, thread_id: str) -> str:
        """Get WebSocket URL for a thread's browser stream.
        
        Args:
            thread_id: Unique thread identifier
            
        Returns:
            str: WebSocket URL (e.g., ws://localhost:9223)
        """
        port = self.get_port_for_thread(thread_id)
        return f"ws://localhost:{port}"
    
    def release_port(self, thread_id: str) -> None:
        """Release a port when thread is closed.
        
        Args:
            thread_id: Unique thread identifier
        """
        if thread_id in self._active_ports:
            del self._active_ports[thread_id]
    
    def is_active(self, thread_id: str) -> bool:
        """Check if a thread has an active stream.
        
        Args:
            thread_id: Unique thread identifier
            
        Returns:
            bool: True if thread has active stream
        """
        return thread_id in self._active_ports
    
    def get_active_streams(self) -> Dict[str, int]:
        """Get all active stream ports.
        
        Returns:
            Dict[str, int]: Mapping of thread IDs to ports
        """
        return self._active_ports.copy()


# Global stream manager instance
stream_manager = StreamManager()
