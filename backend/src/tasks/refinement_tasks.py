"""Celery tasks for automated model refinement."""

from __future__ import annotations

from celery import Celery

from ..config import get_settings
from ..database import _session_factory
from ..services.model_refinement import ModelRefinementService
from ..utils.logging import get_logger

_logger = get_logger(component="refinement_tasks")
_settings = get_settings()

# Celery app (shared with other tasks)
from ..tasks.scoring_tasks import celery_app


@celery_app.task(name="check_model_performance")
def task_check_model_performance(model_version: str = "v1.0") -> dict[str, Any]:
    """Celery task to check model performance."""
    import asyncio
    
    async def _check():
        async with _session_factory() as session:  # type: ignore[call-arg]
            refinement = ModelRefinementService(session)
            result = await refinement.check_model_performance(model_version=model_version)
            return result
    
    return asyncio.run(_check())


@celery_app.task(name="automated_refinement_check")
def task_automated_refinement_check() -> dict[str, Any]:
    """Celery task for automated refinement check (run weekly)."""
    import asyncio
    
    async def _check():
        async with _session_factory() as session:  # type: ignore[call-arg]
            refinement = ModelRefinementService(session)
            result = await refinement.automated_refinement_check()
            return result
    
    return asyncio.run(_check())


# Celery beat schedule for automated refinement
CELERY_BEAT_SCHEDULE_REFINEMENT = {
    "weekly-refinement-check": {
        "task": "automated_refinement_check",
        "schedule": 604800.0,  # Weekly (7 days)
    },
}

