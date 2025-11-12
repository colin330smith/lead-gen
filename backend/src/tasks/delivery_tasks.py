"""Celery tasks for automated lead delivery."""

from __future__ import annotations

from celery import Celery

from ..config import get_settings
from ..database import _session_factory
from ..services.delivery_orchestrator import DeliveryOrchestrator
from ..utils.logging import get_logger

_logger = get_logger(component="delivery_tasks")
_settings = get_settings()

# Celery app (shared with scoring_tasks)
from ..tasks.scoring_tasks import celery_app


@celery_app.task(name="deliver_assigned_leads")
def task_deliver_assigned_leads(
    contractor_id: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Celery task to deliver assigned leads."""
    import asyncio
    
    async def _deliver():
        async with _session_factory() as session:  # type: ignore[call-arg]
            orchestrator = DeliveryOrchestrator(session)
            result = await orchestrator.deliver_assigned_leads(
                contractor_id=contractor_id,
                limit=limit,
            )
            return result
    
    return asyncio.run(_deliver())


@celery_app.task(name="deliver_single_lead")
def task_deliver_single_lead(
    lead_id: int,
    delivery_methods: list[str] | None = None,
) -> dict[str, Any]:
    """Celery task to deliver a single lead."""
    import asyncio
    
    async def _deliver():
        async with _session_factory() as session:  # type: ignore[call-arg]
            orchestrator = DeliveryOrchestrator(session)
            result = await orchestrator.deliver_lead(
                lead_id=lead_id,
                delivery_methods=delivery_methods,
            )
            return result
    
    return asyncio.run(_deliver())


# Celery beat schedule for automated delivery
CELERY_BEAT_SCHEDULE_DELIVERY = {
    "deliver-assigned-leads-hourly": {
        "task": "deliver_assigned_leads",
        "schedule": 3600.0,  # Every hour
    },
}

