"""
Rate Limiting Middleware
Prevents API abuse and ensures fair resource usage
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status

from app.config import settings

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"] if settings.rate_limit_enabled else []
)


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key from request
    
    Uses user ID if authenticated, otherwise IP address
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.get("user_id")
        if user_id:
            return f"user:{user_id}"
    
    # Fallback to IP address
    return get_remote_address(request)


# Custom rate limit exceeded handler
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded: {exc.detail}",
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"}
    )
