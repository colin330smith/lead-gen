"""FastAPI endpoints for feedback collection."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.feedback_collector import FeedbackCollector
from ..services.performance_analytics import PerformanceAnalytics
from ..utils.logging import get_logger

_logger = get_logger(component="feedback_api")

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("/lead/{lead_id}")
async def submit_feedback(
    lead_id: int,
    contractor_id: int = Query(..., description="Contractor ID"),
    outcome: str = Query(..., description="won, lost, no_response, not_interested, wrong_lead"),
    converted: bool = Query(False, description="Whether lead converted"),
    conversion_value: float | None = Query(None, description="Revenue if converted"),
    lead_quality_rating: int | None = Query(None, ge=1, le=5, description="Lead quality rating (1-5)"),
    accuracy_rating: int | None = Query(None, ge=1, le=5, description="Accuracy rating (1-5)"),
    contact_quality_rating: int | None = Query(None, ge=1, le=5, description="Contact quality rating (1-5)"),
    feedback_text: str | None = Query(None, description="Free-form feedback"),
    notes: str | None = Query(None, description="Additional notes"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Submit feedback for a lead."""
    try:
        collector = FeedbackCollector(session)
        feedback = await collector.submit_feedback(
            lead_id=lead_id,
            contractor_id=contractor_id,
            outcome=outcome,
            converted=converted,
            conversion_value=conversion_value,
            lead_quality_rating=lead_quality_rating,
            accuracy_rating=accuracy_rating,
            contact_quality_rating=contact_quality_rating,
            feedback_text=feedback_text,
            notes=notes,
        )
        
        return {
            "id": feedback.id,
            "lead_id": feedback.lead_id,
            "contractor_id": feedback.contractor_id,
            "outcome": feedback.outcome,
            "converted": feedback.converted,
            "conversion_value": feedback.conversion_value,
            "submitted_at": feedback.submitted_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _logger.exception("Error submitting feedback", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_feedback_stats(
    contractor_id: int | None = Query(None, description="Filter by contractor"),
    trade: str | None = Query(None, description="Filter by trade"),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get feedback statistics."""
    try:
        collector = FeedbackCollector(session)
        
        date_from_obj = datetime.fromisoformat(date_from) if date_from else None
        date_to_obj = datetime.fromisoformat(date_to) if date_to else None
        
        stats = await collector.get_feedback_stats(
            contractor_id=contractor_id,
            trade=trade,
            date_from=date_from_obj,
            date_to=date_to_obj,
        )
        
        return stats
    except Exception as e:
        _logger.exception("Error getting feedback stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/score-accuracy")
async def get_score_accuracy(
    trade: str | None = Query(None, description="Filter by trade"),
    min_feedback_count: int = Query(10, ge=1, description="Minimum feedback count"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get score accuracy analysis."""
    try:
        analytics = PerformanceAnalytics(session)
        analysis = await analytics.analyze_score_accuracy(
            trade=trade,
            min_feedback_count=min_feedback_count,
        )
        return analysis
    except Exception as e:
        _logger.exception("Error analyzing score accuracy", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/feature-importance")
async def get_feature_importance(
    trade: str | None = Query(None, description="Filter by trade"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get feature importance analysis."""
    try:
        analytics = PerformanceAnalytics(session)
        analysis = await analytics.analyze_feature_importance(trade=trade)
        return analysis
    except Exception as e:
        _logger.exception("Error analyzing feature importance", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance")
async def get_model_performance(
    trade: str | None = Query(None, description="Filter by trade"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get overall model performance summary."""
    try:
        analytics = PerformanceAnalytics(session)
        summary = await analytics.get_model_performance_summary(trade=trade)
        return summary
    except Exception as e:
        _logger.exception("Error getting performance summary", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

