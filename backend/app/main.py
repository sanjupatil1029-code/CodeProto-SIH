from contextlib import asynccontextmanager
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core import database
from app.core.redis import test_redis_connection

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up NIRVAAN backend...")
    
    # Test DB connection and fallback if needed
    db_ok = await database.check_and_fallback_db()
    if db_ok:
        await database.init_db()
        
    # Test Redis connection
    await test_redis_connection()
    
    yield
    
    # Shutdown actions
    logger.info("Shutting down NIRVAAN backend...")
    await database.engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API service for Industrial Approval & Compliance Orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Refine for production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.router import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify system status."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "project": settings.PROJECT_NAME
    }

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to NIRVAAN API",
        "docs_url": "/docs",
        "health_check": "/health"
    }
