"""
Database Initialization Script
Creates database tables and default admin user
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import init_db, SessionLocal
from app.db.models import User, UserRole
from app.auth.jwt import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_default_admin():
    """Create default admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            logger.info("default_admin_exists", extra_fields={"username": "admin"})
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@wardenxt.local",
            hashed_password=get_password_hash("admin123"),  # Change in production!
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        
        logger.info(
            "default_admin_created",
            extra_fields={
                "username": "admin",
                "email": "admin@wardenxt.local",
                "warning": "Default password is 'admin123' - CHANGE IN PRODUCTION!"
            }
        )
        
        print("✓ Default admin user created:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  ⚠️  WARNING: Change this password in production!")
        
    except Exception as e:
        logger.error("admin_creation_failed", extra_fields={"error": str(e)}, exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Initialize database"""
    try:
        logger.info("initializing_database")
        print("Initializing database...")
        
        # Create tables
        init_db()
        print("✓ Database tables created")
        
        # Create default admin
        create_default_admin()
        
        print("\n✓ Database initialization complete!")
        
    except Exception as e:
        logger.error("database_init_failed", extra_fields={"error": str(e)}, exc_info=True)
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
