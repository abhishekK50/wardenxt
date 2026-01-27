"""
Status Management API Routes
Endpoints for incident status tracking and updates
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Dict
import json

from app.models.incident import (
    IncidentStatus, StatusUpdateRequest, StatusUpdate, IncidentSummary
)
from app.core.data_loader import DataLoader
from app.db.status_store import get_status_store
from app.core.agent.status_stream import get_status_stream
from app.auth.dependencies import get_current_user_dependency, require_incident_manager, get_user_from_token_or_query

router = APIRouter(prefix="/status", tags=["status"])

# Initialize services
data_loader = DataLoader()
status_store = get_status_store()
status_stream = get_status_stream()


@router.get("/{incident_id}")
async def get_incident_status(
    incident_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get current status of an incident
    
    Args:
        incident_id: Incident identifier
        
    Returns:
        Current status and history
    """
    try:
        # Load incident to verify it exists
        incident = data_loader.load_incident(incident_id)
        
        # Get current status (from persistent store or default)
        current_status = status_store.get_current_status(incident_id)
        if current_status is None:
            current_status = incident.summary.status
            # Initialize if not exists
            status_store.initialize_status(incident_id, current_status)
        
        # Get status history
        history = status_store.get_status_history(incident_id)
        
        return {
            "incident_id": incident_id,
            "current_status": current_status.value if hasattr(current_status, 'value') else str(current_status),
            "status_history": [h.model_dump() for h in history],
            "last_updated": history[-1].timestamp if history else incident.summary.start_time
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{incident_id}/update")
async def update_incident_status(
    incident_id: str,
    request: StatusUpdateRequest,
    current_user: dict = Depends(require_incident_manager)
):
    """Update incident status
    
    Args:
        incident_id: Incident identifier
        request: Status update request
        
    Returns:
        Updated status information
    """
    try:
        # Load incident to verify it exists
        incident = data_loader.load_incident(incident_id)
        
        # Get current status
        current_status = status_store.get_current_status(incident_id)
        if current_status is None:
            current_status = incident.summary.status
        
        # Validate status transition (optional business logic)
        # You could add rules like: DETECTED -> INVESTIGATING only
        
        # Add status update to persistent store
        status_update = status_store.add_status_update(
            incident_id=incident_id,
            from_status=current_status,
            to_status=request.new_status,
            updated_by=request.updated_by,
            notes=request.notes
        )
        
        return {
            "success": True,
            "incident_id": incident_id,
            "previous_status": current_status.value if hasattr(current_status, 'value') else str(current_status),
            "new_status": request.new_status.value if hasattr(request.new_status, 'value') else str(request.new_status),
            "update": status_update.model_dump()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/history")
async def get_status_history(
    incident_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get complete status history for an incident
    
    Args:
        incident_id: Incident identifier
        
    Returns:
        List of all status changes
    """
    try:
        # Load incident to verify it exists
        incident = data_loader.load_incident(incident_id)
        
        # Get history from persistent store
        history = status_store.get_status_history(incident_id)
        
        return {
            "incident_id": incident_id,
            "status_changes": len(history),
            "history": [h.model_dump() for h in history]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/initialize")
async def initialize_all_statuses(
    current_user: dict = Depends(require_incident_manager)
):
    """Initialize status for all incidents
    Useful for setting initial state for existing incidents
    
    Returns:
        Number of incidents initialized
    """
    try:
        incident_ids = data_loader.list_incidents()
        
        initialized_count = 0
        for incident_id in incident_ids:
            if status_store.get_current_status(incident_id) is None:
                incident = data_loader.load_incident(incident_id)
                status_store.initialize_status(incident_id, incident.summary.status)
                initialized_count += 1
        
        return {
            "success": True,
            "total_incidents": len(incident_ids),
            "initialized": initialized_count,
            "message": f"Initialized {initialized_count} incident statuses"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/agent/stream")
async def stream_agent_status(
    incident_id: str,
    current_user: dict = Depends(get_user_from_token_or_query)
):
    """Stream real-time agent status updates using Server-Sent Events

    EventSource doesn't support custom headers, so authentication token
    can be provided via query parameter: ?token=<jwt_token>

    Args:
        incident_id: Incident identifier

    Returns:
        SSE stream of agent status updates
    """
    async def event_generator():
        """Generate SSE events"""
        try:
            async for update in status_stream.stream_updates(incident_id):
                # Format as SSE
                data = json.dumps(update)
                yield f"data: {data}\n\n"
        except Exception as e:
            # Send error and close
            error_data = json.dumps({
                "error": str(e),
                "type": "error"
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )