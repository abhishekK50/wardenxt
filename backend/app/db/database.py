"""
Database Connection and Session Management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings
from app.db.models import Base

# For SQLite (development)
if settings.database_url.startswith("sqlite"):
    # SQLite needs special handling for async
    sync_engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.app_debug
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    
    # Async engine for SQLite
    async_database_url = settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.app_debug,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL or other databases
    sync_engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.app_debug
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    
    # Async engine
    async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
        echo=settings.app_debug
    )

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=sync_engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncSession:
    """Async dependency for getting database session
    
    Yields:
        Async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
