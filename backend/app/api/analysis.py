"""
Analysis API Routes
Endpoints for AI-powered incident analysis
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict

from app.models.analysis import (
    IncidentBrief, AnalysisRequest, AnalysisResponse, AgentStatus
)
from app.core.data_loader import DataLoader
from app.core.agent.analyzer import IncidentAnalyzer

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize services
data_loader = DataLoader()
analyzer = IncidentAnalyzer()

# Cache for generated briefs (in production, use Redis)
brief_cache: Dict[str, IncidentBrief] = {}


@router.post("/{incident_id}/analyze", response_model=IncidentBrief)
async def analyze_incident(
    incident_id: str,
    request: AnalysisRequest = None
):
    """Analyze incident using Gemini 3 AI
    
    This is the CORE feature - Total Recall Context + AI Analysis
    
    Args:
        incident_id: Incident to analyze
        request: Analysis configuration
        
    Returns:
        AI-generated incident brief
    """
    # Check cache first
    if incident_id in brief_cache:
        return brief_cache[incident_id]
    
    try:
        # Load incident data
        incident = data_loader.load_incident(incident_id)
        
        # Set max_logs from request or default
        max_logs = request.max_logs if request else 1000
        
        # Analyze using Gemini 3
        brief = await analyzer.analyze_incident(incident, max_logs=max_logs)
        
        # Cache result
        brief_cache[incident_id] = brief
        
        return brief
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/brief", response_model=IncidentBrief)
async def get_cached_brief(incident_id: str):
    """Get cached analysis brief (if available)
    
    Args:
        incident_id: Incident identifier
        
    Returns:
        Cached incident brief or 404
    """
    if incident_id not in brief_cache:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Call /analyze first."
        )
    
    return brief_cache[incident_id]


@router.get("/agent/status", response_model=AgentStatus)
async def get_agent_status():
    """Get current AI agent status
    
    Returns:
        Current agent status
    """
    return analyzer.get_agent_status()


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