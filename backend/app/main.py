"""
WardenXT FastAPI Application
Main application entry point
"""


import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import sqlalchemy as sa

from app.config import settings, validate_security_settings
from app.api import incidents, analysis, status, auth
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.core.logging import setup_logging, get_logger
from app.db.database import init_db

# Setup logging
logger = setup_logging()
logger.info("application_started", extra_fields={"environment": settings.app_env}) 

# Create FastAPI app
app = FastAPI(
    title="WardenXT API",
    description="AI-Powered Incident Commander - Gemini 3 Hackathon Project",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Security headers middleware (add first)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and validate configuration on application startup"""
    try:
        # Validate security settings first
        validate_security_settings()
        logger.info("security_settings_validated")

        # Initialize database
        init_db()
        logger.info("database_initialized")
    except ValueError as e:
        logger.error("configuration_validation_failed", extra_fields={"error": str(e)})
        raise
    except Exception as e:
        logger.error("startup_failed", extra_fields={"error": str(e)})
        raise

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(status.router, prefix="/api")




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
    from app.db.database import sync_engine
    
    # Check database connection
    db_status = "healthy"
    try:
        with sync_engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error("health_check_db_failed", extra_fields={"error": str(e)})
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "gemini_model": settings.gemini_model,
        "environment": settings.app_env,
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with logging"""
    logger.error(
        "unhandled_exception",
        extra_fields={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
            "error_type": type(exc).__name__
        },
        exc_info=True
    )
    
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