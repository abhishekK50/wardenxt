"""
Analysis API Routes
Endpoints for AI-powered incident analysis
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from typing import Dict, Tuple
from datetime import datetime, timedelta
from slowapi import Limiter

from app.middleware.rate_limit import limiter
from app.auth.dependencies import get_current_user_dependency
from app.core.audit import audit_log, get_client_ip, get_user_agent

from app.models.analysis import (
    IncidentBrief, AnalysisRequest, AnalysisResponse, AgentStatus
)
from app.core.data_loader import DataLoader
from app.core.agent.analyzer import IncidentAnalyzer

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize services
data_loader = DataLoader()
analyzer = IncidentAnalyzer()


def get_webhook_incident_data():
    """Import webhook incident data storage (avoid circular import)"""
    from app.api.webhooks import webhook_incidents, webhook_incident_data
    return webhook_incidents, webhook_incident_data

# Cache for generated briefs with TTL (timestamp, brief)
# In production, use Redis for distributed caching
CACHE_TTL_MINUTES = 60  # Cache expires after 1 hour
brief_cache: Dict[str, Tuple[datetime, IncidentBrief]] = {}


def _get_from_cache(incident_id: str) -> IncidentBrief | None:
    """Get brief from cache if not expired"""
    if incident_id not in brief_cache:
        return None

    timestamp, brief = brief_cache[incident_id]
    if datetime.now() - timestamp > timedelta(minutes=CACHE_TTL_MINUTES):
        # Expired, remove from cache
        del brief_cache[incident_id]
        return None

    return brief


def _set_in_cache(incident_id: str, brief: IncidentBrief):
    """Set brief in cache with current timestamp"""
    brief_cache[incident_id] = (datetime.now(), brief)

    # Simple cache eviction: keep only last 100 entries
    if len(brief_cache) > 100:
        # Remove oldest entries
        sorted_keys = sorted(brief_cache.keys(), key=lambda k: brief_cache[k][0])
        for key in sorted_keys[:20]:  # Remove oldest 20
            del brief_cache[key]


@router.post("/{incident_id}/analyze", response_model=IncidentBrief)
@limiter.limit("10/minute")
async def analyze_incident(
    request: Request,
    incident_id: str,
    analysis_request: AnalysisRequest = None,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Analyze incident using Gemini 3 AI

    This is the CORE feature - Total Recall Context + AI Analysis

    Args:
        incident_id: Incident to analyze
        request: Analysis configuration

    Returns:
        AI-generated incident brief
    """
    # Check cache first (with TTL check)
    cached_brief = _get_from_cache(incident_id)
    if cached_brief:
        return cached_brief

    try:
        # Load incident data - check webhook incidents first
        webhook_incidents_dict, webhook_incident_data_dict = get_webhook_incident_data()
        if incident_id in webhook_incident_data_dict:
            incident = webhook_incident_data_dict[incident_id]
        else:
            # Fall back to file-based incidents
            incident = data_loader.load_incident(incident_id)

        # Set max_logs from request or default
        max_logs = analysis_request.max_logs if analysis_request else 1000

        # Audit log
        audit_log(
            action="incident_analysis_started",
            user_id=current_user.get("user_id"),
            username=current_user.get("username"),
            resource_type="incident",
            resource_id=incident_id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            db=None  # Will be added when we have db session
        )

        # Analyze using Gemini 3
        brief = await analyzer.analyze_incident(incident, max_logs=max_logs)

        # Cache result with TTL
        _set_in_cache(incident_id, brief)

        return brief
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/brief", response_model=IncidentBrief)
async def get_cached_brief(
    incident_id: str,
    current_user: dict = Depends(get_current_user_dependency)
):
    """Get cached analysis brief (if available)

    Args:
        incident_id: Incident identifier

    Returns:
        Cached incident brief or 404
    """
    cached_brief = _get_from_cache(incident_id)
    if not cached_brief:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found or expired. Call /analyze first."
        )

    return cached_brief


@router.get("/agent/status", response_model=AgentStatus)
async def get_agent_status():
    """Get current AI agent status
    
    Returns:
        Current agent status
    """
    return analyzer.get_agent_status()


@router.get("/{incident_id}/agent/status", response_model=AgentStatus)
async def get_incident_agent_status(incident_id: str):
    """Get agent status for a specific incident
    
    Args:
        incident_id: Incident identifier
        
    Returns:
        Current agent status for the incident
    """
    from app.core.agent.status_stream import get_status_stream
    status_stream = get_status_stream()
    status = status_stream.get_current_status(incident_id)
    
    if status is None:
        return AgentStatus(status="IDLE", progress=0.0)
    
    return status


@router.delete("/{incident_id}/brief")
async def clear_cached_brief(incident_id: str):
    """Clear cached brief to force re-analysis
    
    Args:
        incident_id: Incident identifier
        
    Returns:
        Success message
    """
    if incident_id in brief_cache:
        del brief_cache[incident_id]
        return {"message": "Cache cleared", "incident_id": incident_id}
    else:
        raise HTTPException(status_code=404, detail="No cached brief found")