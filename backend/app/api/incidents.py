"""
Incidents API Routes
Endpoints for incident data access
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List

from app.models.incident import Incident, IncidentListItem
from app.core.data_loader import DataLoader
from app.auth.dependencies import get_current_user_dependency, get_optional_user

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Initialize data loader
data_loader = DataLoader()


def get_webhook_incidents():
    """Import webhook incidents storage (avoid circular import)"""
    from app.api.webhooks import webhook_incidents, webhook_incident_data
    return webhook_incidents, webhook_incident_data

@router.get("/")
async def list_incidents(current_user: dict = Depends(get_optional_user)):
    """List all available incidents with summaries (both file-based and webhook-ingested)"""
    try:
        incidents = []

        # Get file-based incidents
        incident_ids = data_loader.list_incidents()
        for incident_id in incident_ids:
            try:
                incident = data_loader.load_incident(incident_id)
                incidents.append(incident.summary)
            except Exception as e:
                continue

        # Get webhook-ingested incidents
        webhook_incidents_dict, _ = get_webhook_incidents()
        for external_inc in webhook_incidents_dict.values():
            incidents.append(external_inc.incident_data)

        return {"incidents": incidents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: str,
    include_logs: bool = Query(True, description="Include log entries"),
    include_metrics: bool = Query(True, description="Include metrics"),
    max_logs: int = Query(1000, description="Maximum logs to return"),
    current_user: dict = Depends(get_optional_user)
):
    """Get complete incident data (file-based or webhook-ingested)

    Args:
        incident_id: Incident identifier
        include_logs: Whether to include logs
        include_metrics: Whether to include metrics
        max_logs: Maximum number of logs

    Returns:
        Complete incident data
    """
    try:
        # First, try webhook incidents
        webhook_incidents_dict, webhook_incident_data = get_webhook_incidents()
        if incident_id in webhook_incident_data:
            incident = webhook_incident_data[incident_id]
        else:
            # Fall back to file-based incidents
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
    current_user: dict = Depends(get_optional_user)
):
    """Get incident summary only (lightweight)

    Args:
        incident_id: Incident identifier

    Returns:
        Incident summary
    """
    try:
        # Check webhook incidents first
        webhook_incidents_dict, webhook_incident_data = get_webhook_incidents()
        if incident_id in webhook_incident_data:
            incident = webhook_incident_data[incident_id]
        else:
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
    current_user: dict = Depends(get_optional_user)
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
        # Check webhook incidents first
        webhook_incidents_dict, webhook_incident_data = get_webhook_incidents()
        if incident_id in webhook_incident_data:
            incident = webhook_incident_data[incident_id]
        else:
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
    current_user: dict = Depends(get_optional_user)
):
    """Get incident metrics

    Args:
        incident_id: Incident identifier
        limit: Maximum metrics to return

    Returns:
        List of metric points
    """
    try:
        # Check webhook incidents first
        webhook_incidents_dict, webhook_incident_data = get_webhook_incidents()
        if incident_id in webhook_incident_data:
            incident = webhook_incident_data[incident_id]
        else:
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
    current_user: dict = Depends(get_optional_user)
):
    """Get incident timeline

    Args:
        incident_id: Incident identifier

    Returns:
        Timeline events
    """
    try:
        # Check webhook incidents first
        webhook_incidents_dict, webhook_incident_data = get_webhook_incidents()
        if incident_id in webhook_incident_data:
            incident = webhook_incident_data[incident_id]
        else:
            incident = data_loader.load_incident(incident_id)

        return incident.timeline

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent/list")
async def get_recent_incidents(
    limit: int = Query(5, description="Maximum incidents to return", ge=1, le=50),
    current_user: dict = Depends(get_optional_user)
):
    """Get recent incidents for live feed (sorted by creation time)

    Args:
        limit: Maximum number of incidents to return (1-50)

    Returns:
        List of recent incidents
    """
    try:
        incidents_with_time = []

        # Get file-based incidents
        incident_ids = data_loader.list_incidents()
        for incident_id in incident_ids:
            try:
                incident = data_loader.load_incident(incident_id)
                incidents_with_time.append({
                    "summary": incident.summary,
                    "created_at": incident.summary.start_time or incident.summary.detection_time or "",
                    "source": "manual"
                })
            except Exception:
                continue

        # Get webhook-ingested incidents
        webhook_incidents_dict, _ = get_webhook_incidents()
        for external_inc in webhook_incidents_dict.values():
            incidents_with_time.append({
                "summary": external_inc.incident_data,
                "created_at": external_inc.created_at,
                "source": external_inc.source,
                "auto_analyzed": external_inc.auto_analyzed
            })

        # Sort by created_at descending (newest first)
        incidents_with_time.sort(key=lambda x: x["created_at"], reverse=True)

        # Take top N
        recent_incidents = incidents_with_time[:limit]

        # Format response
        return {
            "total": len(incidents_with_time),
            "limit": limit,
            "incidents": [
                {
                    "incident_id": inc["summary"].incident_id,
                    "title": inc["summary"].title,
                    "severity": inc["summary"].severity,
                    "status": inc["summary"].status,
                    "created_at": inc["created_at"],
                    "source": inc.get("source", "manual"),
                    "auto_analyzed": inc.get("auto_analyzed", False),
                    "services_affected": inc["summary"].services_affected
                }
                for inc in recent_incidents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))