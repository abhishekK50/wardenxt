"""
WardenXT FastAPI Application
Main application entry point
"""


import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import incidents, analysis

# Create FastAPI app
app = FastAPI(
    title="WardenXT API",
    description="AI-Powered Incident Commander - Gemini 3 Hackathon Project",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")





@app.get("/api/incidents/")
async def list_incidents():
    """List all available incidents with full metadata"""
    output_dir = Path(__file__).parent.parent / "data-generation" / "output"
    
    if not output_dir.exists():
        return {"incidents": []}
    
    incidents = []
    for incident_dir in output_dir.iterdir():
        if incident_dir.is_dir():
            summary_file = incident_dir / "summary.json"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    incident_data = json.load(f)
                    incidents.append(incident_data)
    
    # Sort by incident_id descending (newest first)
    incidents.sort(key=lambda x: x.get('incident_id', ''), reverse=True)
    
    return {"incidents": incidents}






@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "WardenXT API",
        "version": "1.0.0",
        "description": "AI-Powered Incident Commander using Gemini 3",
        "features": {
            "total_recall": settings.enable_total_recall,
            "visual_debug": settings.enable_visual_debug,
            "agentic_actions": settings.enable_agentic_actions,
            "change_sentinel": settings.enable_change_sentinel
        },
        "endpoints": {
            "docs": "/docs",
            "incidents": "/api/incidents",
            "analysis": "/api/analysis"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_model": settings.gemini_model,
        "environment": settings.app_env
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.app_debug else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug
    )