"""FastAPI endpoints for lead management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.lead import Lead
from ..services.lead_generation import LeadGenerationService
from ..utils.logging import get_logger

_logger = get_logger(component="leads_api")

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


@router.get("/")
async def list_leads(
    trade: str | None = Query(None, description="Filter by trade"),
    status: str | None = Query(None, description="Filter by status"),
    contractor_id: int | None = Query(None, description="Filter by contractor"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum intent score"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """List leads with filtering."""
    try:
        query = select(Lead).where(Lead.intent_score >= min_score)
        
        if trade:
            query = query.where(Lead.trade == trade)
        
        if status:
            query = query.where(Lead.status == status)
        
        if contractor_id:
            query = query.where(Lead.contractor_id == contractor_id)
        
        query = query.order_by(Lead.intent_score.desc()).limit(limit).offset(offset)
        
        result = await session.execute(query)
        leads = result.scalars().all()
        
        # Get total count
        count_query = select(Lead).where(Lead.intent_score >= min_score)
        if trade:
            count_query = count_query.where(Lead.trade == trade)
        if status:
            count_query = count_query.where(Lead.status == status)
        if contractor_id:
            count_query = count_query.where(Lead.contractor_id == contractor_id)
        
        from sqlalchemy import func
        total_result = await session.execute(select(func.count()).select_from(count_query))
        total = total_result.scalar() or 0
        
        return {
            "leads": [
                {
                    "id": lead.id,
                    "prop_id": lead.prop_id,
                    "trade": lead.trade,
                    "intent_score": lead.intent_score,
                    "quality_score": lead.quality_score,
                    "status": lead.status,
                    "zip_code": lead.zip_code,
                    "market_value": lead.market_value,
                    "signal_count": lead.signal_count,
                    "generated_at": lead.generated_at.isoformat(),
                    "contractor_id": lead.contractor_id,
                }
                for lead in leads
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        _logger.exception("Error listing leads", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_leads(
    trade: str = Query(..., description="Trade type (roofing, hvac, siding, electrical)"),
    min_score: float = Query(0.6, ge=0.0, le=1.0, description="Minimum intent score"),
    max_leads: int | None = Query(None, ge=1, le=10000, description="Maximum leads to generate"),
    zip_codes: list[str] | None = Query(None, description="Filter by ZIP codes"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Generate new leads for a trade."""
    try:
        service = LeadGenerationService(session)
        leads = await service.generate_leads(
            trade=trade,
            min_score=min_score,
            max_leads=max_leads,
            zip_codes=zip_codes,
        )
        
        return {
            "generated": len(leads),
            "trade": trade,
            "leads": [
                {
                    "id": lead.id,
                    "prop_id": lead.prop_id,
                    "intent_score": lead.intent_score,
                    "quality_score": lead.quality_score,
                }
                for lead in leads
            ],
        }
    except Exception as e:
        _logger.exception("Error generating leads", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/assign")
async def assign_lead(
    lead_id: int,
    contractor_id: int = Query(..., description="Contractor ID"),
    assigned_by: str = Query("system", description="Who assigned the lead"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Assign a lead to a contractor."""
    try:
        service = LeadGenerationService(session)
        lead = await service.assign_lead_to_contractor(
            lead_id=lead_id,
            contractor_id=contractor_id,
            assigned_by=assigned_by,
        )
        
        return {
            "id": lead.id,
            "status": lead.status,
            "contractor_id": lead.contractor_id,
            "assigned_at": lead.assigned_at.isoformat() if lead.assigned_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.exception("Error assigning lead", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/deliver")
async def deliver_lead(
    lead_id: int,
    delivery_method: str = Query("api", description="Delivery method"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Mark a lead as delivered."""
    try:
        service = LeadGenerationService(session)
        lead = await service.mark_lead_delivered(lead_id=lead_id, delivery_method=delivery_method)
        
        return {
            "id": lead.id,
            "status": lead.status,
            "delivered_at": lead.delivered_at.isoformat() if lead.delivered_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.exception("Error delivering lead", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: int,
    conversion_value: float | None = Query(None, description="Conversion value (revenue)"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Mark a lead as converted."""
    try:
        service = LeadGenerationService(session)
        lead = await service.mark_lead_converted(lead_id=lead_id, conversion_value=conversion_value)
        
        return {
            "id": lead.id,
            "status": lead.status,
            "converted_at": lead.converted_at.isoformat() if lead.converted_at else None,
            "conversion_value": lead.conversion_value,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.exception("Error converting lead", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}")
async def get_lead(
    lead_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get a single lead by ID."""
    try:
        lead = await session.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return {
            "id": lead.id,
            "prop_id": lead.prop_id,
            "trade": lead.trade,
            "intent_score": lead.intent_score,
            "quality_score": lead.quality_score,
            "status": lead.status,
            "contractor_id": lead.contractor_id,
            "zip_code": lead.zip_code,
            "market_value": lead.market_value,
            "signal_count": lead.signal_count,
            "violation_count": lead.violation_count,
            "request_count": lead.request_count,
            "generated_at": lead.generated_at.isoformat(),
            "assigned_at": lead.assigned_at.isoformat() if lead.assigned_at else None,
            "delivered_at": lead.delivered_at.isoformat() if lead.delivered_at else None,
            "converted_at": lead.converted_at.isoformat() if lead.converted_at else None,
            "metadata": lead.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("Error getting lead", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

