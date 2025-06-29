"""Database configuration for PostgreSQL."""
import os
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Database configuration
class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self):
        # Get database settings from environment variables
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'jobs_scraper')
        self.username = os.getenv('DB_USER', 'scraper_user')
        self.password = os.getenv('DB_PASSWORD', 'scraper_password')
        
        # Database URLs
        self.database_url = os.getenv(
            'DATABASE_URL',
            f'postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'
        )
        self.async_database_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    @property
    def sync_engine_kwargs(self) -> dict:
        """Synchronous engine configuration."""
        return {
            'echo': os.getenv('DEBUG', 'false').lower() == 'true',
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }
    
    @property
    def async_engine_kwargs(self) -> dict:
        """Asynchronous engine configuration."""
        return {
            'echo': os.getenv('DEBUG', 'false').lower() == 'true',
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        }


# Global database configuration instance
db_config = DatabaseConfig()

# SQLAlchemy base for ORM models
Base = declarative_base()

# Create engines
sync_engine = create_engine(db_config.database_url, **db_config.sync_engine_kwargs)

# For async operations (if needed)
try:
    async_engine = create_async_engine(db_config.async_database_url, **db_config.async_engine_kwargs)
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
except Exception:
    # Fallback if asyncpg is not available
    async_engine = None
    AsyncSessionLocal = None

# Session factory for synchronous operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def get_database_session():
    """Get a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def get_async_database_session():
    """Get an async database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async session not available. Install asyncpg: pip install asyncpg")
    
    async with AsyncSessionLocal() as session:
        yield session


def test_connection() -> bool:
    """Test database connection."""
    try:
        with sync_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False


def create_tables():
    """Create all tables defined in the Base metadata."""
    try:
        Base.metadata.create_all(bind=sync_engine)
        print("Database tables created successfully.")
        return True
    except Exception as e:
        print(f"Failed to create tables: {e}")
        return False


def drop_tables():
    """Drop all tables defined in the Base metadata."""
    try:
        Base.metadata.drop_all(bind=sync_engine)
        print("Database tables dropped successfully.")
        return True
    except Exception as e:
        print(f"Failed to drop tables: {e}")
        return False 