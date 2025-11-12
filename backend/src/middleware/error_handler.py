"""Error handling middleware and utilities."""

from __future__ import annotations

import traceback
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from ..utils.logging import get_logger

_logger = get_logger(component="error_handler")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for FastAPI."""
    _logger.exception(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        traceback=traceback.format_exc(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if str(exc) else "An unexpected error occurred",
            "path": request.url.path,
        },
    )


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors."""
    _logger.error(
        "Database error",
        path=request.url.path,
        error=str(exc),
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error",
            "message": "A database error occurred. Please try again later.",
            "path": request.url.path,
        },
    )


async def validation_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle validation errors."""
    _logger.warning(
        "Validation error",
        path=request.url.path,
        error=str(exc),
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "message": str(exc),
            "path": request.url.path,
        },
    )

