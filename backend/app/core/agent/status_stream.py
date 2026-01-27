"""
Agent Status Stream
Real-time status updates for agent analysis progress
"""

import asyncio
import json
from typing import AsyncIterator, Dict, Optional, List
from datetime import datetime

from app.core.logging import get_logger

from app.models.analysis import AgentStatus


class AgentStatusStream:
    """Manages real-time agent status streaming"""
    
    def __init__(self):
        """Initialize status stream"""
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self._current_statuses: Dict[str, AgentStatus] = {}
        self.logger = get_logger(__name__)
    
    def subscribe(self, incident_id: str) -> asyncio.Queue:
        """Subscribe to status updates for an incident
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            Queue to receive status updates
        """
        if incident_id not in self._subscribers:
            self._subscribers[incident_id] = asyncio.Queue()
        return self._subscribers[incident_id]
    
    def unsubscribe(self, incident_id: str):
        """Unsubscribe from status updates
        
        Args:
            incident_id: Incident identifier
        """
        if incident_id in self._subscribers:
            del self._subscribers[incident_id]
    
    async def update_status(
        self,
        incident_id: str,
        status: str,
        current_task: Optional[str] = None,
        progress: float = 0.0,
        logs_analyzed: int = 0,
        metrics_analyzed: int = 0,
        reasoning_steps: Optional[List[str]] = None
    ):
        """Update agent status and notify subscribers
        
        Args:
            incident_id: Incident identifier
            status: Current status
            current_task: Current task description
            progress: Progress (0.0-1.0)
            logs_analyzed: Number of logs analyzed
            metrics_analyzed: Number of metrics analyzed
            reasoning_steps: List of reasoning steps
        """
        agent_status = AgentStatus(
            status=status,
            current_task=current_task,
            progress=progress,
            logs_analyzed=logs_analyzed,
            metrics_analyzed=metrics_analyzed,
            insights_generated=0
        )
        
        self._current_statuses[incident_id] = agent_status
        
        # Create update message
        update = {
            'incident_id': incident_id,
            'status': agent_status.model_dump(),
            'reasoning_steps': reasoning_steps or [],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Notify all subscribers
        if incident_id in self._subscribers:
            try:
                await self._subscribers[incident_id].put(update)
            except Exception as e:
                self.logger.error(
                    "status_update_failed",
                    extra_fields={
                        "incident_id": incident_id,
                        "error": str(e)
                    }
                )
    
    def get_current_status(self, incident_id: str) -> Optional[AgentStatus]:
        """Get current status for an incident
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            Current AgentStatus or None
        """
        return self._current_statuses.get(incident_id)
    
    async def stream_updates(self, incident_id: str) -> AsyncIterator[Dict]:
        """Stream status updates for an incident
        
        Args:
            incident_id: Incident identifier
            
        Yields:
            Status update dictionaries
        """
        queue = self.subscribe(incident_id)
        
        try:
            # Send initial status if available
            current = self.get_current_status(incident_id)
            if current:
                yield {
                    'incident_id': incident_id,
                    'status': current.model_dump(),
                    'reasoning_steps': [],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            
            # Stream updates
            while True:
                try:
                    # Wait for update with timeout
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield update
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield {
                        'type': 'heartbeat',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
        finally:
            self.unsubscribe(incident_id)


# Global instance
_status_stream: Optional[AgentStatusStream] = None

def get_status_stream() -> AgentStatusStream:
    """Get global status stream instance"""
    global _status_stream
    if _status_stream is None:
        _status_stream = AgentStatusStream()
    return _status_stream
