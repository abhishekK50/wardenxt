"""
Structured Logging Configuration
Replaces print() statements with proper structured logging
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict
import json
from datetime import datetime

from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class CustomAdapter(logging.LoggerAdapter):
    """
    Adapter to handle extra_fields argument by moving it to extra dict
    """
    def process(self, msg, kwargs):
        if 'extra_fields' in kwargs:
            extra = kwargs.get('extra', {})
            if not isinstance(extra, dict):
                 extra = {}
            # Verify if extra is the MutableMapping or similar if needed, 
            # but usually it's a dict. 
            # We must be careful not to overwrite existing extra if it is not a dict (unlikely).
            
            # Add extra_fields to extra
            extra['extra_fields'] = kwargs.pop('extra_fields')
            kwargs['extra'] = extra
        return msg, kwargs


def setup_logging():
    """Setup structured logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use JSON formatter in production, simple formatter in development
    if settings.app_env == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Return matched adapter instead of raw logger
    return CustomAdapter(root_logger, {})


def get_logger(name: str = None) -> logging.LoggerAdapter:
    """Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name or "wardenxt")
    return CustomAdapter(logger, {})


# Initialize logging on import
logger = setup_logging()
