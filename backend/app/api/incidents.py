"""
Incidents API Routes
Endpoints for incident data access
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List

from app.models.incident import Incident, IncidentListItem
from app.core.data_loader import DataLoader
from app.auth.dependencies import get_current_user_dependency

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Initialize data loader
data_loader = DataLoader()

@router.get("/")
async def list_incidents(current_user: dict = Depends(get_current_user_dependency)):
    """List all available incidents with summaries"""
    try:
        incident_ids = data_loader.list_incidents()
        incidents = []

        for incident_id in incident_ids:
            try:
                incident = data_loader.load_incident(incident_id)
                incidents.append(incident.summary)
            except Exception as e:
                continue

        return {"incidents": incidents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: str,
    include_logs: bool = Query(True, description="Include log entries"),
    include_metrics: bool = Query(True, description="Include metrics"),
    max_logs: int = Query(1000, description="Maximum logs to return"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get complete incident data
    
    Args:
        incident_id: Incident identifier
        include_logs: Whether to include logs
        include_metrics: Whether to include metrics
        max_logs: Maximum number of logs
        
    Returns:
        Complete incident data
    """
    try:
        incident = data_loader.load_incident(incident_id)
        
        # Optionally filter data
        if not include_logs:
            incident.logs = []
        elif len(incident.logs) > max_logs:
            incident.logs = incident.logs[:max_logs]
        
        if not include_metrics:
            incident.metrics = []
        
        return incident
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/summary")
async def get_incident_summary(
    incident_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get incident summary only (lightweight)
    
    Args:
        incident_id: Incident identifier
        
    Returns:
        Incident summary
    """
    try:
        incident = data_loader.load_incident(incident_id)
        return incident.summary
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/logs")
async def get_incident_logs(
    incident_id: str,
    level: str = Query(None, description="Filter by log level"),
    limit: int = Query(100, description="Maximum logs to return"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get incident logs with optional filtering
    
    Args:
        incident_id: Incident identifier
        level: Optional log level filter (ERROR, WARN, etc.)
        limit: Maximum logs to return
        
    Returns:
        List of log entries
    """
    try:
        incident = data_loader.load_incident(incident_id)
        logs = incident.logs
        
        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.level == level.upper()]
        
        # Apply limit
        logs = logs[:limit]
        
        return logs
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/metrics")
async def get_incident_metrics(
    incident_id: str,
    limit: int = Query(100, description="Maximum metrics to return"),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get incident metrics
    
    Args:
        incident_id: Incident identifier
        limit: Maximum metrics to return
        
    Returns:
        List of metric points
    """
    try:
        incident = data_loader.load_incident(incident_id)
        metrics = incident.metrics[:limit]
        
        return metrics
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get incident timeline
    
    Args:
        incident_id: Incident identifier
        
    Returns:
        Timeline events
    """
    try:
        incident = data_loader.load_incident(incident_id)
        return incident.timeline
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))