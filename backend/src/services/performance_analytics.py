"""Performance analytics service for model evaluation."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feedback import LeadFeedback
from ..models.lead import Lead
from ..models.lead_score import LeadScore
from ..utils.logging import get_logger

_logger = get_logger(component="performance_analytics")


class PerformanceAnalytics:
    """Service for analyzing model performance and conversion rates."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_score_accuracy(
        self,
        trade: str | None = None,
        min_feedback_count: int = 10,
    ) -> dict[str, Any]:
        """
        Analyze how well intent scores predict conversions.
        
        Returns calibration data showing conversion rates by score ranges.
        """
        _logger.info("Analyzing score accuracy", trade=trade)
        
        # Get leads with feedback
        query = (
            select(Lead, LeadScore, LeadFeedback)
            .join(LeadScore, Lead.prop_id == LeadScore.prop_id)
            .join(LeadFeedback, Lead.id == LeadFeedback.lead_id)
        )
        
        if trade:
            query = query.where(Lead.trade == trade, LeadScore.trade == trade)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        if len(rows) < min_feedback_count:
            return {
                "error": f"Insufficient feedback data (need {min_feedback_count}, have {len(rows)})",
                "data_points": len(rows),
            }
        
        # Group by score ranges
        score_ranges = {
            "0.0-0.3": {"min": 0.0, "max": 0.3, "leads": [], "converted": 0},
            "0.3-0.5": {"min": 0.3, "max": 0.5, "leads": [], "converted": 0},
            "0.5-0.7": {"min": 0.5, "max": 0.7, "leads": [], "converted": 0},
            "0.7-0.9": {"min": 0.7, "max": 0.9, "leads": [], "converted": 0},
            "0.9-1.0": {"min": 0.9, "max": 1.0, "leads": [], "converted": 0},
        }
        
        for lead, score, feedback in rows:
            score_value = score.intent_score
            for range_name, range_data in score_ranges.items():
                if range_data["min"] <= score_value < range_data["max"]:
                    range_data["leads"].append(lead.id)
                    if feedback.converted:
                        range_data["converted"] += 1
                    break
        
        # Calculate conversion rates
        calibration_data = {}
        for range_name, range_data in score_ranges.items():
            total = len(range_data["leads"])
            converted = range_data["converted"]
            conversion_rate = (converted / total * 100) if total > 0 else 0.0
            
            calibration_data[range_name] = {
                "total_leads": total,
                "converted": converted,
                "conversion_rate": round(conversion_rate, 2),
                "expected_rate": round((range_data["min"] + range_data["max"]) / 2 * 100, 2),
            }
        
        # Overall metrics
        total_leads = sum(d["total_leads"] for d in calibration_data.values())
        total_converted = sum(d["converted"] for d in calibration_data.values())
        overall_conversion_rate = (total_converted / total_leads * 100) if total_leads > 0 else 0.0
        
        return {
            "trade": trade or "all",
            "total_leads": total_leads,
            "total_converted": total_converted,
            "overall_conversion_rate": round(overall_conversion_rate, 2),
            "calibration_data": calibration_data,
            "data_points": len(rows),
        }

    async def analyze_feature_importance(
        self,
        trade: str | None = None,
    ) -> dict[str, Any]:
        """Analyze which features correlate most with conversions."""
        _logger.info("Analyzing feature importance", trade=trade)
        
        # Get leads with feedback and scores
        query = (
            select(Lead, LeadScore, LeadFeedback)
            .join(LeadScore, Lead.prop_id == LeadScore.prop_id)
            .join(LeadFeedback, Lead.id == LeadFeedback.lead_id)
        )
        
        if trade:
            query = query.where(Lead.trade == trade, LeadScore.trade == trade)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        if len(rows) < 20:
            return {
                "error": "Insufficient data for feature importance analysis",
                "data_points": len(rows),
            }
        
        # Analyze correlations
        converted_scores = []
        non_converted_scores = []
        
        converted_signals = []
        non_converted_signals = []
        
        converted_violations = []
        non_converted_violations = []
        
        for lead, score, feedback in rows:
            if feedback.converted:
                converted_scores.append(score.intent_score)
                converted_signals.append(lead.signal_count or 0)
                converted_violations.append(lead.violation_count or 0)
            else:
                non_converted_scores.append(score.intent_score)
                non_converted_signals.append(lead.signal_count or 0)
                non_converted_violations.append(lead.violation_count or 0)
        
        # Calculate averages
        avg_converted_score = sum(converted_scores) / len(converted_scores) if converted_scores else 0
        avg_non_converted_score = sum(non_converted_scores) / len(non_converted_scores) if non_converted_scores else 0
        
        avg_converted_signals = sum(converted_signals) / len(converted_signals) if converted_signals else 0
        avg_non_converted_signals = sum(non_converted_signals) / len(non_converted_signals) if non_converted_signals else 0
        
        avg_converted_violations = sum(converted_violations) / len(converted_violations) if converted_violations else 0
        avg_non_converted_violations = sum(non_converted_violations) / len(non_converted_violations) if non_converted_violations else 0
        
        return {
            "trade": trade or "all",
            "data_points": len(rows),
            "feature_importance": {
                "intent_score": {
                    "converted_avg": round(avg_converted_score, 4),
                    "non_converted_avg": round(avg_non_converted_score, 4),
                    "difference": round(avg_converted_score - avg_non_converted_score, 4),
                },
                "signal_count": {
                    "converted_avg": round(avg_converted_signals, 2),
                    "non_converted_avg": round(avg_non_converted_signals, 2),
                    "difference": round(avg_converted_signals - avg_non_converted_signals, 2),
                },
                "violation_count": {
                    "converted_avg": round(avg_converted_violations, 2),
                    "non_converted_avg": round(avg_non_converted_violations, 2),
                    "difference": round(avg_converted_violations - avg_non_converted_violations, 2),
                },
            },
        }

    async def get_model_performance_summary(
        self,
        trade: str | None = None,
    ) -> dict[str, Any]:
        """Get overall model performance summary."""
        # Get conversion stats
        feedback_stats = await self.analyze_score_accuracy(trade=trade)
        feature_importance = await self.analyze_feature_importance(trade=trade)
        
        return {
            "trade": trade or "all",
            "score_accuracy": feedback_stats,
            "feature_importance": feature_importance,
        }

