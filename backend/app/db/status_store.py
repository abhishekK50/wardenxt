"""
Status Store
Persistent storage for incident status history
Uses JSON file-based storage (can be upgraded to SQLite later)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from app.core.logging import get_logger

from app.models.incident import IncidentStatus, StatusUpdate


class StatusStore:
    """Persistent storage for incident status history"""
    
    def __init__(self, storage_path: str = "./data/status_history"):
        """Initialize status store
        
        Args:
            storage_path: Path to store status history files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        
        # In-memory cache for current statuses
        self._current_statuses: Dict[str, IncidentStatus] = {}
        self._load_current_statuses()
    
    def _get_status_file(self, incident_id: str) -> Path:
        """Get path to status history file for an incident"""
        return self.storage_path / f"{incident_id}.json"
    
    def _load_current_statuses(self):
        """Load current statuses from all history files"""
        if not self.storage_path.exists():
            return
        
        for status_file in self.storage_path.glob("*.json"):
            try:
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    if data.get('history'):
                        last_update = data['history'][-1]
                        incident_id = status_file.stem
                        self._current_statuses[incident_id] = IncidentStatus(last_update['to_status'])
            except Exception as e:
                self.logger.warning("status_load_error", extra_fields={"file": str(status_file), "error": str(e)})
    
    def get_current_status(self, incident_id: str) -> Optional[IncidentStatus]:
        """Get current status for an incident
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            Current status or None if not found
        """
        return self._current_statuses.get(incident_id)
    
    def get_status_history(self, incident_id: str) -> List[StatusUpdate]:
        """Get complete status history for an incident
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            List of status updates
        """
        status_file = self._get_status_file(incident_id)
        
        if not status_file.exists():
            return []
        
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                history = data.get('history', [])
                
                # Convert to StatusUpdate objects
                return [
                    StatusUpdate(
                        timestamp=item['timestamp'],
                        from_status=IncidentStatus(item['from_status']),
                        to_status=IncidentStatus(item['to_status']),
                        updated_by=item.get('updated_by', 'System'),
                        notes=item.get('notes')
                    )
                    for item in history
                ]
        except Exception as e:
            self.logger.error("status_history_load_failed", extra_fields={"incident_id": incident_id, "error": str(e)})
            return []
    
    def add_status_update(
        self,
        incident_id: str,
        from_status: IncidentStatus,
        to_status: IncidentStatus,
        updated_by: str = "System",
        notes: Optional[str] = None
    ) -> StatusUpdate:
        """Add a new status update
        
        Args:
            incident_id: Incident identifier
            from_status: Previous status
            to_status: New status
            updated_by: User who made the update
            notes: Optional notes
            
        Returns:
            Created StatusUpdate
        """
        status_file = self._get_status_file(incident_id)
        
        # Load existing history
        history = []
        if status_file.exists():
            try:
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    history = data.get('history', [])
            except Exception:
                history = []
        
        # Create new update
        update = StatusUpdate(
            timestamp=datetime.utcnow().isoformat() + "Z",
            from_status=from_status,
            to_status=to_status,
            updated_by=updated_by,
            notes=notes
        )
        
        # Add to history
        history.append({
            'timestamp': update.timestamp,
            'from_status': update.from_status.value,
            'to_status': update.to_status.value,
            'updated_by': update.updated_by,
            'notes': update.notes
        })
        
        # Save to file
        try:
            with open(status_file, 'w') as f:
                json.dump({
                    'incident_id': incident_id,
                    'history': history,
                    'last_updated': update.timestamp
                }, f, indent=2)
            
            # Update cache
            self._current_statuses[incident_id] = to_status
            
            return update
        except Exception as e:
            self.logger.error("status_update_save_failed", extra_fields={"incident_id": incident_id, "error": str(e)}, exc_info=True)
            raise
    
    def initialize_status(
        self,
        incident_id: str,
        initial_status: IncidentStatus = IncidentStatus.DETECTED
    ):
        """Initialize status for a new incident
        
        Args:
            incident_id: Incident identifier
            initial_status: Initial status
        """
        if incident_id not in self._current_statuses:
            self.add_status_update(
                incident_id=incident_id,
                from_status=IncidentStatus.DETECTED,
                to_status=initial_status,
                updated_by="System",
                notes="Initial status"
            )


# Global instance
_status_store: Optional[StatusStore] = None

def get_status_store() -> StatusStore:
    """Get global status store instance"""
    global _status_store
    if _status_store is None:
        _status_store = StatusStore()
    return _status_store
