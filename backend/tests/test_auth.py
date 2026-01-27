"""
Authentication Tests
"""

import pytest
from app.auth.jwt import create_access_token, decode_access_token, verify_password, get_password_hash
from app.db.models import User, UserRole
from app.api.auth import register_user, login


def test_password_hashing():
    """Test password hashing and verification"""
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_token_creation():
    """Test JWT token creation"""
    data = {"sub": "testuser", "user_id": 1, "roles": ["admin"]}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_token_decoding():
    """Test JWT token decoding"""
    data = {"sub": "testuser", "user_id": 1, "roles": ["admin"]}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    
    assert decoded["sub"] == "testuser"
    assert decoded["user_id"] == 1
    assert "admin" in decoded["roles"]


def test_invalid_token():
    """Test invalid token handling"""
    with pytest.raises(Exception):  # Should raise HTTPException
        decode_access_token("invalid_token")


def test_user_registration(client, db_session):
    """Test user registration"""
    # First, create an admin user for registration
    from app.db.models import User
    from app.auth.jwt import get_password_hash
    
    admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    
    # Get admin token
    admin_token = create_access_token(
        data={"sub": "admin", "user_id": admin.id, "roles": ["admin"]}
    )
    
    # Register new user
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
            "role": "viewer"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 201
    assert response.json()["username"] == "newuser"


def test_user_login(client, db_session):
    """Test user login"""
    from app.db.models import User
    from app.auth.jwt import get_password_hash
    
    # Create test user
    user = User(
        username="testuser",
        email="test@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Login
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "nonexistent",
            "password": "wrong"
        }
    )
    
    assert response.status_code == 401
