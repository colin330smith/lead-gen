"""Celery tasks for automated scoring and lead generation."""

from __future__ import annotations

from datetime import datetime

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import _session_factory
from ..services.lead_generation import LeadGenerationService
from ..services.score_scheduler import recalculate_scores
from ..utils.logging import get_logger

_logger = get_logger(component="scoring_tasks")
_settings = get_settings()

# Celery app (will be configured with Redis)
celery_app = Celery(
    "local_lift",
    broker=_settings.redis_url if hasattr(_settings, "redis_url") else "redis://localhost:6379/0",
    backend=_settings.redis_url if hasattr(_settings, "redis_url") else "redis://localhost:6379/0",
)


@celery_app.task(name="recalculate_scores")
def task_recalculate_scores(trade: str | None = None, limit: int | None = None) -> dict[str, Any]:
    """Celery task to recalculate scores."""
    import asyncio
    
    async def _recalculate():
        async with _session_factory() as session:  # type: ignore[call-arg]
            stats = await recalculate_scores(session, trade=trade, limit=limit)
            return stats
    
    return asyncio.run(_recalculate())


@celery_app.task(name="generate_leads")
def task_generate_leads(
    trade: str,
    min_score: float = 0.6,
    max_leads: int | None = None,
) -> dict[str, Any]:
    """Celery task to generate leads."""
    import asyncio
    
    async def _generate():
        async with _session_factory() as session:  # type: ignore[call-arg]
            service = LeadGenerationService(session)
            leads = await service.generate_leads(
                trade=trade,
                min_score=min_score,
                max_leads=max_leads,
            )
            return {
                "generated": len(leads),
                "trade": trade,
                "lead_ids": [lead.id for lead in leads],
            }
    
    return asyncio.run(_generate())


@celery_app.task(name="daily_scoring_job")
def task_daily_scoring() -> dict[str, Any]:
    """Daily job to recalculate scores for all trades."""
    import asyncio
    
    async def _daily_scoring():
        results = {}
        async with _session_factory() as session:  # type: ignore[call-arg]
            for trade in ["roofing", "hvac", "siding", "electrical"]:
                _logger.info(f"Recalculating scores for {trade}")
                stats = await recalculate_scores(session, trade=trade)
                results[trade] = stats
        return results
    
    return asyncio.run(_daily_scoring())


@celery_app.task(name="daily_lead_generation")
def task_daily_lead_generation() -> dict[str, Any]:
    """Daily job to generate leads for all trades."""
    import asyncio
    
    async def _daily_lead_generation():
        results = {}
        async with _session_factory() as session:  # type: ignore[call-arg]
            service = LeadGenerationService(session)
            for trade in ["roofing", "hvac", "siding", "electrical"]:
                _logger.info(f"Generating leads for {trade}")
                leads = await service.generate_leads(trade=trade, min_score=0.6)
                results[trade] = {"generated": len(leads)}
        return results
    
    return asyncio.run(_daily_lead_generation())


# Celery beat schedule (configured in celeryconfig.py or main app)
CELERY_BEAT_SCHEDULE = {
    "daily-scoring": {
        "task": "recalculate_scores",
        "schedule": 86400.0,  # Daily
    },
    "daily-lead-generation": {
        "task": "generate_leads",
        "schedule": 86400.0,  # Daily
    },
}

