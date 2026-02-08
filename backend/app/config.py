"""
WardenXT Configuration Module
Centralized configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Gemini API Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp",
        env="GEMINI_MODEL"
    )
    
    # Application Settings
    app_env: str = Field(default="development", env="APP_ENV")
    app_debug: bool = Field(default=True, env="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./wardenxt.db",
        env="DATABASE_URL"
    )
    
    # Vector Store Configuration
    vector_store_path: str = Field(
        default="./data/vector_store",
        env="VECTOR_STORE_PATH"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/wardenxt.log", env="LOG_FILE")
    
    # Authentication & Security
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production-use-openssl-rand-hex-32",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, env="JWT_EXPIRE_MINUTES")  # 24 hours
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # CORS Settings - simplified for .env parsing
    cors_origins: str = Field(
        default='["http://localhost:3000","http://localhost:8000"]',
        env="CORS_ORIGINS"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string"""
        import json
        if isinstance(self.cors_origins, str):
            return json.loads(self.cors_origins)
        return self.cors_origins
    
    # Feature Flags
    enable_total_recall: bool = Field(default=True, env="ENABLE_TOTAL_RECALL")
    enable_visual_debug: bool = Field(default=True, env="ENABLE_VISUAL_DEBUG")
    enable_agentic_actions: bool = Field(default=True, env="ENABLE_AGENTIC_ACTIONS")
    enable_change_sentinel: bool = Field(default=False, env="ENABLE_CHANGE_SENTINEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection for FastAPI"""
    return settings


# Lazy validation - only check when actually needed
def validate_gemini_key():
    """Validate Gemini API key is configured (called when needed, not on import)"""
    if not settings.gemini_api_key or settings.gemini_api_key == "your_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY not configured! Please set it in backend/.env or environment variables"
        )
    return True


def validate_security_settings():
    """Validate critical security settings on startup"""
    errors = []

    # Check JWT secret key in production
    if settings.app_env == "production":
        if settings.jwt_secret_key == "change-this-secret-key-in-production-use-openssl-rand-hex-32":
            errors.append(
                "CRITICAL: JWT_SECRET_KEY is using the default value in production! "
                "Generate a secure key with: openssl rand -hex 32"
            )

        if settings.app_debug:
            errors.append(
                "WARNING: APP_DEBUG is True in production environment! "
                "Set APP_DEBUG=false in production"
            )

    # Check JWT secret key length
    if len(settings.jwt_secret_key) < 32:
        errors.append(
            "WARNING: JWT_SECRET_KEY is too short (< 32 characters). "
            "Use a longer secret for better security."
        )

    if errors:
        error_message = "\n".join(errors)
        # For hackathon demo, just warn but don't fail
        import warnings
        warnings.warn(f"Security warnings:\n{error_message}", UserWarning)

    return True