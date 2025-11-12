from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings
from .models.base import Base
from .models.property import Property  # noqa: F401 - Import to register with Base.metadata
from .models.zip_code_tier import ZipCodeTier  # noqa: F401 - Import to register with Base.metadata
from .models.contact_enrichment import ContactEnrichment  # noqa: F401 - Import to register with Base.metadata
from .models.code_violation import CodeViolation  # noqa: F401 - Import to register with Base.metadata
from .models.storm_event import StormEvent  # noqa: F401 - Import to register with Base.metadata
from .models.service_request import ServiceRequest  # noqa: F401 - Import to register with Base.metadata
from .models.deed_record import DeedRecord  # noqa: F401 - Import to register with Base.metadata
from .models.lead_score import LeadScore  # noqa: F401 - Import to register with Base.metadata
from .models.lead import Lead  # noqa: F401 - Import to register with Base.metadata
from .models.contractor import Contractor, ContractorTerritory  # noqa: F401 - Import to register with Base.metadata
from .models.engagement import DeliveryLog, LeadEngagement  # noqa: F401 - Import to register with Base.metadata
from .models.feedback import ABTest, LeadFeedback, ModelVersion  # noqa: F401 - Import to register with Base.metadata
from .utils.logging import get_logger

_logger = get_logger(component="database")

_settings = get_settings()
_engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    echo=_settings.database_echo,
    pool_pre_ping=True,
)
_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-style dependency for acquiring an async session."""

    async with _session_factory() as session:  # type: ignore[call-arg]
        yield session


async def init_database() -> None:
    """Initialize database connection (test connection)."""

    try:
        async with _engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - logged for operator visibility
        _logger.exception("Failed to connect to database")
        raise


async def create_tables() -> None:
    """Create all database tables defined in models."""

    # First check if table exists using a separate connection
    async with _engine.connect() as check_conn:
        result = await check_conn.execute(
            text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'properties')"
            )
        )
        table_exists = result.scalar()
    
    if table_exists:
        _logger.info("Database tables already exist, skipping creation")
        return
    
    # Try to create tables
    try:
        async with _engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            _logger.info("Database tables created successfully")
    except Exception as e:
        # If objects already exist (from partial creation), verify table exists
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str:
            _logger.warning(f"Some database objects may already exist: {e}")
            # Verify table was created using a new connection
            async with _engine.connect() as verify_conn:
                result = await verify_conn.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'properties')"
                    )
                )
                if result.scalar():
                    _logger.info("Properties table exists, proceeding with ingestion")
                else:
                    _logger.error("Table creation failed and table does not exist")
                    raise
        else:
            _logger.exception("Failed to create database tables")
            raise


__all__ = ["get_session", "init_database", "create_tables", "_engine", "_session_factory"]
