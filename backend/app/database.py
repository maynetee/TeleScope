from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from app.config import get_settings
import os
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def create_engine_for_database():
    """Create the appropriate async engine based on database configuration."""
    if settings.use_sqlite:
        # SQLite configuration (for local development)
        os.makedirs("data", exist_ok=True)
        logger.info("Using SQLite database for local development")
        return create_async_engine(
            settings.database_url,
            echo=settings.app_debug,
            future=True,
            connect_args={
                "timeout": 30,
                "check_same_thread": False,
            },
        )
    else:
        # PostgreSQL configuration (production)
        logger.info(f"Connecting to PostgreSQL at {settings.postgres_host}:{settings.postgres_port}")
        return create_async_engine(
            settings.database_url,
            echo=settings.app_debug,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
        )


# Create async engine
engine = create_engine_for_database()


# SQLite-specific pragmas (only applied when using SQLite)
if settings.use_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables.

    Note: In production with PostgreSQL, prefer using Alembic migrations.
    This function is kept for development and initial setup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")
