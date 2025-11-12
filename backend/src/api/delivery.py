"""FastAPI endpoints for lead delivery."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.delivery_orchestrator import DeliveryOrchestrator
from ..services.engagement_tracker import EngagementTracker
from ..utils.logging import get_logger

_logger = get_logger(component="delivery_api")

router = APIRouter(prefix="/api/v1/delivery", tags=["delivery"])


@router.post("/lead/{lead_id}")
async def deliver_lead(
    lead_id: int,
    delivery_methods: list[str] | None = Query(None, description="Delivery methods (email, webhook)"),
    webhook_url: str | None = Query(None, description="Optional webhook URL"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Deliver a single lead."""
    try:
        orchestrator = DeliveryOrchestrator(session)
        result = await orchestrator.deliver_lead(
            lead_id=lead_id,
            delivery_methods=delivery_methods,
            webhook_url=webhook_url,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.exception("Error delivering lead", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assigned")
async def deliver_assigned_leads(
    contractor_id: int | None = Query(None, description="Filter by contractor"),
    limit: int | None = Query(None, ge=1, le=1000, description="Maximum leads to deliver"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Deliver all assigned but not yet delivered leads."""
    try:
        orchestrator = DeliveryOrchestrator(session)
        result = await orchestrator.deliver_assigned_leads(
            contractor_id=contractor_id,
            limit=limit,
        )
        return result
    except Exception as e:
        _logger.exception("Error delivering assigned leads", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engagement/{lead_id}")
async def get_lead_engagement(
    lead_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get engagement statistics for a lead."""
    try:
        tracker = EngagementTracker(session)
        stats = await tracker.get_lead_engagement_stats(lead_id)
        return stats
    except Exception as e:
        _logger.exception("Error getting engagement stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track/email-open")
async def track_email_open(
    lead_id: int = Query(...),
    tracking_id: str = Query(...),
    user_agent: str | None = Query(None),
    ip_address: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Track email open event."""
    try:
        tracker = EngagementTracker(session)
        engagement = await tracker.track_email_open(
            lead_id=lead_id,
            tracking_id=tracking_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return {
            "id": engagement.id,
            "lead_id": engagement.lead_id,
            "engagement_type": engagement.engagement_type,
            "engaged_at": engagement.engaged_at.isoformat(),
        }
    except Exception as e:
        _logger.exception("Error tracking email open", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track/email-click")
async def track_email_click(
    lead_id: int = Query(...),
    tracking_id: str = Query(...),
    click_url: str = Query(...),
    user_agent: str | None = Query(None),
    ip_address: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Track email click event."""
    try:
        tracker = EngagementTracker(session)
        engagement = await tracker.track_email_click(
            lead_id=lead_id,
            tracking_id=tracking_id,
            click_url=click_url,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return {
            "id": engagement.id,
            "lead_id": engagement.lead_id,
            "engagement_type": engagement.engagement_type,
            "engaged_at": engagement.engaged_at.isoformat(),
        }
    except Exception as e:
        _logger.exception("Error tracking email click", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

