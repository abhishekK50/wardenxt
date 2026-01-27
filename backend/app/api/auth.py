"""
Authentication API Routes
User registration, login, and token management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.database import get_db
from app.db.models import User, UserRole
from app.auth.jwt import create_access_token, verify_password, get_password_hash
from app.auth.dependencies import get_current_user_dependency
from app.core.logging import get_logger
from app.core.audit import audit_log

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
logger = get_logger(__name__)


class UserCreate(BaseModel):
    """User registration request"""
    username: str
    email: EmailStr
    password: str
    full_name: str = None
    role: UserRole = UserRole.VIEWER


class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User response"""
    id: int
    username: str
    email: str
    full_name: str = None
    role: str
    is_active: bool


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency)
):
    """Register a new user (admin only)
    
    Args:
        user_data: User registration data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created user information
    """
    # Check if user is admin
    if current_user.get("roles", []) != ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )
    
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(
        "user_created",
        extra_fields={
            "user_id": new_user.id,
            "username": new_user.username,
            "created_by": current_user.get("username")
        }
    )
    
    audit_log(
        action="user_created",
        user_id=current_user.get("user_id"),
        username=current_user.get("username"),
        resource_type="user",
        resource_id=str(new_user.id),
        details={"username": new_user.username, "role": new_user.role.value}
    )
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role.value,
        is_active=new_user.is_active
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token
    
    Args:
        login_data: Login credentials
        db: Database session
        
    Returns:
        Access token and user information
    """
    # Find user
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user:
        logger.warning("login_failed", extra_fields={"username": login_data.username, "reason": "user_not_found"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        logger.warning("login_failed", extra_fields={"username": login_data.username, "reason": "invalid_password"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning("login_failed", extra_fields={"username": login_data.username, "reason": "user_inactive"})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "email": user.email,
            "user_id": user.id,
            "roles": [user.role.value]
        }
    )
    
    logger.info(
        "user_logged_in",
        extra_fields={
            "user_id": user.id,
            "username": user.username
        }
    )
    
    audit_log(
        action="user_login",
        user_id=user.id,
        username=user.username,
        resource_type="auth",
        resource_id=None,
        details={"success": True}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get current user information
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Current user information
    """
    user = db.query(User).filter(User.id == current_user.get("user_id")).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user_dependency)
):
    """Logout user (client should discard token)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(
        "user_logged_out",
        extra_fields={
            "user_id": current_user.get("user_id"),
            "username": current_user.get("username")
        }
    )
    
    audit_log(
        action="user_logout",
        user_id=current_user.get("user_id"),
        username=current_user.get("username"),
        resource_type="auth",
        resource_id=None
    )
    
    return {"message": "Successfully logged out"}
