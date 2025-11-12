"""Dashboard-specific API endpoints for frontend integration."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.lead import Lead
from ..models.contractor import Contractor
from ..services.lead_verification import LeadVerificationService
from ..utils.logging import get_logger

_logger = get_logger(component="dashboard_api")

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    contractor_id: int | None = Query(None, description="Filter by contractor"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get dashboard statistics."""
    try:
        # Lead counts by status
        status_query = select(
            Lead.status,
            func.count(Lead.id).label("count"),
        ).group_by(Lead.status)
        
        if contractor_id:
            status_query = status_query.where(Lead.contractor_id == contractor_id)
        
        status_result = await session.execute(status_query)
        status_counts = {row.status: row.count for row in status_result.fetchall()}
        
        # Lead counts by trade
        trade_query = select(
            Lead.trade,
            func.count(Lead.id).label("count"),
        ).group_by(Lead.trade)
        
        if contractor_id:
            trade_query = trade_query.where(Lead.contractor_id == contractor_id)
        
        trade_result = await session.execute(trade_query)
        trade_counts = {row.trade: row.count for row in trade_result.fetchall()}
        
        # Recent leads (last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_query = select(func.count(Lead.id)).where(Lead.generated_at >= recent_date)
        if contractor_id:
            recent_query = recent_query.where(Lead.contractor_id == contractor_id)
        recent_result = await session.execute(recent_query)
        recent_count = recent_result.scalar() or 0
        
        # Conversion rate
        total_delivered = status_counts.get("delivered", 0) + status_counts.get("converted", 0)
        converted = status_counts.get("converted", 0)
        conversion_rate = (converted / total_delivered * 100) if total_delivered > 0 else 0.0
        
        # Average intent score
        avg_score_query = select(func.avg(Lead.intent_score))
        if contractor_id:
            avg_score_query = avg_score_query.where(Lead.contractor_id == contractor_id)
        avg_score_result = await session.execute(avg_score_query)
        avg_intent_score = float(avg_score_result.scalar() or 0.0)
        
        return {
            "leads_by_status": status_counts,
            "leads_by_trade": trade_counts,
            "recent_leads_7d": recent_count,
            "conversion_rate": round(conversion_rate, 2),
            "avg_intent_score": round(avg_intent_score, 4),
            "total_leads": sum(status_counts.values()),
        }
    except Exception as e:
        _logger.exception("Error getting dashboard stats", error=str(e))
        raise


@router.get("/leads/verified")
async def get_verified_leads(
    contractor_id: int | None = Query(None),
    min_verification_score: float = Query(0.6, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get verified leads with quality scores."""
    try:
        # Get leads
        query = select(Lead).where(Lead.quality_score >= min_verification_score)
        
        if contractor_id:
            query = query.where(Lead.contractor_id == contractor_id)
        
        query = query.order_by(Lead.quality_score.desc(), Lead.intent_score.desc()).limit(limit)
        
        result = await session.execute(query)
        leads = result.scalars().all()
        
        # Verify each lead
        verification_service = LeadVerificationService(session)
        verified_leads = []
        
        for lead in leads:
            verification = await verification_service.verify_lead(lead.id)
            if verification.get("verified", False):
                verified_leads.append({
                    "id": lead.id,
                    "prop_id": lead.prop_id,
                    "trade": lead.trade,
                    "intent_score": lead.intent_score,
                    "quality_score": lead.quality_score,
                    "verification_score": verification["scores"]["overall"],
                    "has_contact_data": verification["data_quality"].get("has_contact_data", False),
                    "status": lead.status,
                })
        
        return {
            "leads": verified_leads,
            "total": len(verified_leads),
            "min_verification_score": min_verification_score,
        }
    except Exception as e:
        _logger.exception("Error getting verified leads", error=str(e))
        raise


@router.get("/contractors/{contractor_id}/performance")
async def get_contractor_performance(
    contractor_id: int,
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get contractor performance metrics."""
    try:
        contractor = await session.get(Contractor, contractor_id)
        if not contractor:
            raise ValueError(f"Contractor {contractor_id} not found")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Leads assigned
        assigned_query = select(func.count(Lead.id)).where(
            Lead.contractor_id == contractor_id,
            Lead.assigned_at >= start_date,
        )
        assigned_result = await session.execute(assigned_query)
        leads_assigned = assigned_result.scalar() or 0
        
        # Leads delivered
        delivered_query = select(func.count(Lead.id)).where(
            Lead.contractor_id == contractor_id,
            Lead.delivered_at >= start_date,
        )
        delivered_result = await session.execute(delivered_query)
        leads_delivered = delivered_result.scalar() or 0
        
        # Leads converted
        converted_query = select(
            func.count(Lead.id),
            func.sum(Lead.conversion_value),
        ).where(
            Lead.contractor_id == contractor_id,
            Lead.converted_at >= start_date,
        )
        converted_result = await session.execute(converted_query)
        converted_row = converted_result.first()
        leads_converted = converted_row[0] or 0
        total_revenue = float(converted_row[1] or 0.0)
        
        # Conversion rates
        delivery_rate = (leads_delivered / leads_assigned * 100) if leads_assigned > 0 else 0.0
        conversion_rate = (leads_converted / leads_delivered * 100) if leads_delivered > 0 else 0.0
        
        return {
            "contractor_id": contractor_id,
            "company_name": contractor.company_name,
            "period_days": days,
            "leads_assigned": leads_assigned,
            "leads_delivered": leads_delivered,
            "leads_converted": leads_converted,
            "delivery_rate": round(delivery_rate, 2),
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_lead": round(total_revenue / leads_converted, 2) if leads_converted > 0 else 0.0,
        }
    except Exception as e:
        _logger.exception("Error getting contractor performance", error=str(e))
        raise

