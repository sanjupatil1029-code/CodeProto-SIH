from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.logging import logger

DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

def get_engine_args(url: str):
    if url.startswith("sqlite"):
        return {}
    return {
        "pool_size": 10,
        "max_overflow": 20
    }

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    **get_engine_args(DATABASE_URL)
)

# Create async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Declarative base class for models
class Base(DeclarativeBase):
    pass

async def check_and_fallback_db() -> bool:
    """Test connection to DB and fallback to SQLite if PostgreSQL fails."""
    global engine, SessionLocal
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to the configured database.")
        return True
    except Exception as e:
        if not DATABASE_URL.startswith("sqlite"):
            logger.warning(f"Failed to connect to PostgreSQL at {DATABASE_URL}: {str(e)}")
            sqlite_url = "sqlite+aiosqlite:///./nirvaan.db"
            logger.warning(f"Falling back to local SQLite at {sqlite_url}")
            engine = create_async_engine(
                sqlite_url,
                echo=False,
                future=True
            )
            SessionLocal = async_sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                logger.info("Successfully connected to fallback SQLite database.")
                return True
            except Exception as se:
                logger.critical(f"Failed to connect to fallback SQLite database: {str(se)}")
                return False
        else:
            logger.critical(f"Failed to connect to SQLite database: {str(e)}")
            return False

# Dependency to get async DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction error: {str(e)}")
            raise e
        finally:
            await session.close()

async def init_db():
    """Create database tables if they do not exist."""
    # Import all models to ensure they are registered with Base.metadata
    from app.models.auth import User, RefreshToken
    from app.models.business import Business
    from app.models.rules import DocumentType, ApprovalRule
    from app.models.workflows import BusinessApproval
    from app.models.document import Document
    from app.models.inspection import Inspection
    from app.models.grievance import Grievance
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Handle SQLite column additions for dev db
        if is_sqlite or "sqlite" in str(engine.url):
            new_columns = [
                ("business_approvals", "workflow_id", "VARCHAR(36)"),
                ("business_approvals", "external_system", "VARCHAR(100)"),
                ("business_approvals", "external_reference_id", "VARCHAR(100)"),
                ("business_approvals", "integration_mode", "VARCHAR(50) DEFAULT 'PORTAL_HANDOFF'"),
                ("business_approvals", "official_portal_url", "VARCHAR(500)"),
                ("business_approvals", "submitted_at", "DATETIME"),
                ("business_approvals", "stage_history", "JSON DEFAULT '[]'"),
                ("business_approvals", "additional_metadata", "JSON DEFAULT '{}'"),
                ("business_approvals", "issue_date", "DATETIME"),
                ("business_approvals", "expiry_date", "DATETIME"),
                ("business_approvals", "renewal_start_date", "DATETIME"),
                ("business_approvals", "renewal_deadline", "DATETIME"),
                ("business_approvals", "renewal_status", "VARCHAR(50) DEFAULT 'UP_TO_DATE'"),
                ("business_approvals", "renewal_reminder_days", "INTEGER DEFAULT 30"),
                ("business_approvals", "sla_status", "VARCHAR(50) DEFAULT 'ON_TRACK'"),
                ("business_approvals", "sla_elapsed_percent", "FLOAT DEFAULT 0.0"),
            ]
            for table, col, col_type in new_columns:
                try:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                except Exception:
                    pass
    logger.info("Database tables initialized/verified.")

    # Seed default document types and approval rules
    from app.services.rule_engine_service import RuleEngineService
    async with SessionLocal() as session:
        await RuleEngineService.seed_default_rules(session)

