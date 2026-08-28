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
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized/verified.")

    # Seed default document types and approval rules
    from app.services.rule_engine_service import RuleEngineService
    async with SessionLocal() as session:
        await RuleEngineService.seed_default_rules(session)

