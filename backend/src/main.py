"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .api.scoring import router as scoring_router
from .api.leads import router as leads_router
from .api.contractors import router as contractors_router
from .api.dashboard import router as dashboard_router
from .api.delivery import router as delivery_router
from .api.feedback import router as feedback_router
from .api.calibration import router as calibration_router
from .config import get_settings
from .middleware.error_handler import (
    database_error_handler,
    global_exception_handler,
    validation_error_handler,
)
from .utils.logging import get_logger

_logger = get_logger(component="main")
_settings = get_settings()

app = FastAPI(
    title="Local Lift API",
    description="B2B SaaS lead generation platform for residential contractors",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_error_handler)
app.add_exception_handler(ValueError, validation_error_handler)

# Include routers
app.include_router(scoring_router)
app.include_router(leads_router)
app.include_router(contractors_router)
app.include_router(dashboard_router)
app.include_router(delivery_router)
app.include_router(feedback_router)
app.include_router(calibration_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Local Lift API", "version": "1.0.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

