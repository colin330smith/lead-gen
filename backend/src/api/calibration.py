"""FastAPI endpoints for score calibration and model refinement."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.ab_testing import ABTestingService
from ..services.model_refinement import ModelRefinementService
from ..services.score_calibration import ScoreCalibrationEngine
from ..utils.logging import get_logger

_logger = get_logger(component="calibration_api")

router = APIRouter(prefix="/api/v1/calibration", tags=["calibration"])


@router.get("/adjustments")
async def get_calibration_adjustments(
    trade: str | None = Query(None, description="Filter by trade"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get score calibration adjustments."""
    try:
        calibration = ScoreCalibrationEngine(session)
        adjustments = await calibration.calculate_calibration_adjustments(trade=trade)
        return adjustments
    except Exception as e:
        _logger.exception("Error getting calibration adjustments", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_calibration_recommendations(
    trade: str | None = Query(None, description="Filter by trade"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get calibration recommendations."""
    try:
        calibration = ScoreCalibrationEngine(session)
        recommendations = await calibration.get_calibration_recommendations(trade=trade)
        return recommendations
    except Exception as e:
        _logger.exception("Error getting calibration recommendations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests")
async def create_ab_test(
    test_name: str = Query(...),
    model_a_version: str = Query(...),
    model_b_version: str = Query(...),
    split_ratio: float = Query(0.5, ge=0.1, le=0.9),
    description: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a new A/B test."""
    try:
        ab_service = ABTestingService(session)
        ab_test = await ab_service.create_ab_test(
            test_name=test_name,
            model_a_version=model_a_version,
            model_b_version=model_b_version,
            split_ratio=split_ratio,
            description=description,
        )
        
        return {
            "id": ab_test.id,
            "test_name": ab_test.test_name,
            "status": ab_test.status,
            "created_at": ab_test.created_at.isoformat(),
        }
    except Exception as e:
        _logger.exception("Error creating A/B test", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/start")
async def start_ab_test(
    test_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Start an A/B test."""
    try:
        ab_service = ABTestingService(session)
        ab_test = await ab_service.start_ab_test(test_id)
        
        return {
            "id": ab_test.id,
            "status": ab_test.status,
            "started_at": ab_test.started_at.isoformat() if ab_test.started_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.exception("Error starting A/B test", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/analyze")
async def analyze_ab_test(
    test_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Analyze A/B test results."""
    try:
        ab_service = ABTestingService(session)
        analysis = await ab_service.analyze_ab_test(test_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.exception("Error analyzing A/B test", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/complete")
async def complete_ab_test(
    test_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Complete an A/B test."""
    try:
        ab_service = ABTestingService(session)
        ab_test = await ab_service.complete_ab_test(test_id)
        
        return {
            "id": ab_test.id,
            "status": ab_test.status,
            "winner": ab_test.winner,
            "ended_at": ab_test.ended_at.isoformat() if ab_test.ended_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.exception("Error completing A/B test", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/performance")
async def check_model_performance(
    model_version: str = Query("v1.0", description="Model version"),
    min_feedback_count: int = Query(50, ge=1, description="Minimum feedback count"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Check model performance and get refinement recommendations."""
    try:
        refinement = ModelRefinementService(session)
        performance = await refinement.check_model_performance(
            model_version=model_version,
            min_feedback_count=min_feedback_count,
        )
        return performance
    except Exception as e:
        _logger.exception("Error checking model performance", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/refinement-check")
async def automated_refinement_check(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Run automated refinement check."""
    try:
        refinement = ModelRefinementService(session)
        check_result = await refinement.automated_refinement_check()
        return check_result
    except Exception as e:
        _logger.exception("Error running refinement check", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

