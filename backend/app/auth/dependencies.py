"""
Authentication Dependencies
FastAPI dependencies for authentication and authorization
"""

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from app.auth.jwt import get_current_user

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """FastAPI dependency to get current authenticated user
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Current user information
    """
    token = credentials.credentials
    return get_current_user(token)


def require_role(allowed_roles: List[str]):
    """Dependency factory for role-based access control
    
    Args:
        allowed_roles: List of roles that can access the endpoint
        
    Returns:
        Dependency function that checks user roles
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user_dependency)
    ) -> dict:
        user_roles = current_user.get("roles", [])
        
        # Check if user has any of the allowed roles
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_checker


# Common role dependencies
async def require_admin(
    current_user: dict = Depends(get_current_user_dependency)
) -> dict:
    """Require admin role"""
    return await require_role(["admin"])(current_user)


async def require_incident_manager(
    current_user: dict = Depends(get_current_user_dependency)
) -> dict:
    """Require incident manager or admin role"""
    return await require_role(["admin", "incident_manager"])(current_user)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """Get current user if authenticated, None otherwise

    Useful for endpoints that work both authenticated and unauthenticated
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        return get_current_user(token)
    except HTTPException:
        return None


async def get_user_from_token_or_query(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    token: Optional[str] = Query(None, description="JWT token for SSE authentication")
) -> dict:
    """Get current user from Bearer token or query parameter

    This is needed for SSE endpoints since EventSource doesn't support custom headers

    Args:
        credentials: HTTP Bearer token credentials (from Authorization header)
        token: JWT token from query parameter

    Returns:
        Current user information

    Raises:
        HTTPException: If no valid token provided
    """
    # Try header first
    if credentials:
        return get_current_user(credentials.credentials)

    # Fall back to query parameter
    if token:
        return get_current_user(token)

    # No auth provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide token in Authorization header or ?token= query parameter"
    )
