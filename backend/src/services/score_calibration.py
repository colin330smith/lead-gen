"""Score calibration service for improving prediction accuracy."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feedback import LeadFeedback
from ..models.lead import Lead
from ..models.lead_score import LeadScore
from ..services.performance_analytics import PerformanceAnalytics
from ..utils.logging import get_logger

_logger = get_logger(component="score_calibration")


class ScoreCalibrationEngine:
    """Service for calibrating scores based on actual outcomes."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytics = PerformanceAnalytics(session)

    async def calculate_calibration_adjustments(
        self,
        trade: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate score calibration adjustments based on actual conversion rates.
        
        Returns adjustments to apply to scoring algorithm.
        """
        _logger.info("Calculating calibration adjustments", trade=trade)
        
        # Get score accuracy analysis
        accuracy_data = await self.analytics.analyze_score_accuracy(trade=trade, min_feedback_count=5)
        
        if "error" in accuracy_data:
            return {
                "error": accuracy_data["error"],
                "adjustments": None,
            }
        
        calibration_data = accuracy_data.get("calibration_data", {})
        
        # Calculate adjustments for each score range
        adjustments = {}
        for range_name, range_data in calibration_data.items():
            expected_rate = range_data.get("expected_rate", 0)
            actual_rate = range_data.get("conversion_rate", 0)
            
            if expected_rate > 0:
                # Adjustment factor: how much to multiply score by
                adjustment_factor = actual_rate / expected_rate if expected_rate > 0 else 1.0
                
                # Clamp adjustment to reasonable range (0.5x to 2.0x)
                adjustment_factor = max(0.5, min(2.0, adjustment_factor))
                
                adjustments[range_name] = {
                    "expected_rate": expected_rate,
                    "actual_rate": actual_rate,
                    "adjustment_factor": round(adjustment_factor, 4),
                    "adjustment": round((adjustment_factor - 1.0) * 100, 2),  # Percentage change
                }
        
        return {
            "trade": trade or "all",
            "adjustments": adjustments,
            "overall_accuracy": accuracy_data.get("overall_conversion_rate", 0),
        }

    async def apply_calibration(
        self,
        base_score: float,
        trade: str | None = None,
        calibration_adjustments: dict[str, Any] | None = None,
    ) -> float:
        """
        Apply calibration adjustments to a base score.
        
        Args:
            base_score: Original intent score (0.0 to 1.0)
            trade: Trade type for trade-specific calibration
            calibration_adjustments: Pre-calculated adjustments (optional)
        
        Returns:
            Calibrated score (0.0 to 1.0)
        """
        if calibration_adjustments is None:
            calibration_data = await self.calculate_calibration_adjustments(trade=trade)
            calibration_adjustments = calibration_data.get("adjustments", {})
        
        if not calibration_adjustments:
            return base_score  # No calibration available
        
        # Find which range this score falls into
        for range_name, range_data in calibration_adjustments.items():
            # Parse range (e.g., "0.5-0.7")
            min_score, max_score = map(float, range_name.split("-"))
            
            if min_score <= base_score < max_score:
                adjustment_factor = range_data.get("adjustment_factor", 1.0)
                calibrated_score = base_score * adjustment_factor
                
                # Clamp to valid range
                calibrated_score = max(0.0, min(1.0, calibrated_score))
                
                return calibrated_score
        
        # Default: no adjustment
        return base_score

    async def get_calibration_recommendations(
        self,
        trade: str | None = None,
    ) -> dict[str, Any]:
        """Get recommendations for score calibration."""
        calibration_data = await self.calculate_calibration_adjustments(trade=trade)
        
        if "error" in calibration_data:
            return calibration_data
        
        adjustments = calibration_data.get("adjustments", {})
        
        recommendations = []
        for range_name, range_data in adjustments.items():
            adjustment_pct = range_data.get("adjustment", 0)
            expected = range_data.get("expected_rate", 0)
            actual = range_data.get("actual_rate", 0)
            
            if abs(adjustment_pct) > 10:  # More than 10% difference
                recommendations.append({
                    "score_range": range_name,
                    "issue": f"Expected {expected}% conversion, got {actual}%",
                    "recommendation": f"Adjust scores by {adjustment_pct:+.1f}%",
                    "priority": "high" if abs(adjustment_pct) > 20 else "medium",
                })
        
        return {
            "trade": trade or "all",
            "recommendations": recommendations,
            "calibration_data": calibration_data,
        }

