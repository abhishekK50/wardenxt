"""
WardenXT FastAPI Application
Main application entry point
"""


import json
import time
import psutil
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import sqlalchemy as sa

from app.config import settings, validate_security_settings

# Track application start time for uptime calculation
APP_START_TIME = time.time()
from app.api import incidents, analysis, status, auth, webhooks, voice, runbooks, predictions
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
app.include_router(webhooks.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(runbooks.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")




@app.get("/")
async def root():
    """Root endpoint - API welcome and info"""
    return {
        "message": "WardenXT API - AI-Powered Incident Commander",
        "version": "1.0.0",
        "description": "From reactive firefighting to proactive prevention using Google Gemini 3",
        "powered_by": "Google Gemini 3 Flash",
        "docs": "/docs",
        "health": "/health",
        "features": {
            "ai_analysis": "Analyze thousands of logs in seconds",
            "voice_commander": "Natural language incident queries",
            "auto_runbooks": "Generate executable remediation scripts",
            "predictive_analytics": "Forecast incidents before they occur",
            "real_time_ingestion": "Webhook integration with monitoring tools"
        },
        "endpoints": {
            "incidents": "/api/incidents",
            "analysis": "/api/analysis",
            "predictions": "/api/predictions",
            "voice": "/api/voice",
            "runbooks": "/api/runbooks",
            "webhooks": "/api/webhooks"
        }
    }


def get_uptime() -> str:
    """Calculate application uptime"""
    uptime_seconds = int(time.time() - APP_START_TIME)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def get_memory_usage() -> dict:
    """Get current memory usage"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2)
        }
    except Exception:
        return {"error": "Unable to retrieve memory info"}


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for monitoring"""
    from app.db.database import sync_engine

    # Check database connection
    db_status = "healthy"
    try:
        with sync_engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error("health_check_db_failed", extra_fields={"error": str(e)})

    # Check Gemini API (basic check - just verify config exists)
    gemini_status = "configured" if settings.gemini_api_key else "not_configured"

    # Overall status
    is_healthy = db_status == "healthy" and gemini_status == "configured"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.app_env,
        "uptime": get_uptime(),
        "memory": get_memory_usage(),
        "services": {
            "database": db_status,
            "gemini_api": gemini_status,
            "webhooks": "active",
            "predictions": "running",
            "voice": "active",
            "runbooks": "active"
        },
        "config": {
            "gemini_model": settings.gemini_model,
            "features": {
                "total_recall": settings.enable_total_recall,
                "visual_debug": settings.enable_visual_debug,
                "agentic_actions": settings.enable_agentic_actions,
                "change_sentinel": settings.enable_change_sentinel
            }
        }
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