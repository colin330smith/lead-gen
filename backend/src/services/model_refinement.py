"""Automated model refinement service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.feedback import ModelVersion
from ..services.performance_analytics import PerformanceAnalytics
from ..services.score_calibration import ScoreCalibrationEngine
from ..utils.logging import get_logger

_logger = get_logger(component="model_refinement")


class ModelRefinementService:
    """Service for automated model refinement and retraining."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytics = PerformanceAnalytics(session)
        self.calibration = ScoreCalibrationEngine(session)

    async def check_model_performance(
        self,
        model_version: str = "v1.0",
        min_feedback_count: int = 50,
    ) -> dict[str, Any]:
        """
        Check if model performance has degraded.
        
        Returns performance metrics and recommendations.
        """
        _logger.info("Checking model performance", model_version=model_version)
        
        # Get performance summary
        performance = await self.analytics.get_model_performance_summary()
        
        # Get calibration recommendations
        calibration = await self.calibration.get_calibration_recommendations()
        
        # Check if performance is below threshold
        conversion_rate = performance.get("score_accuracy", {}).get("overall_conversion_rate", 0)
        min_acceptable_rate = 15.0  # 15% minimum conversion rate
        
        needs_refinement = conversion_rate < min_acceptable_rate
        
        recommendations = []
        if needs_refinement:
            recommendations.append({
                "type": "performance_degradation",
                "severity": "high",
                "message": f"Conversion rate ({conversion_rate}%) below threshold ({min_acceptable_rate}%)",
                "action": "Consider model retraining or calibration",
            })
        
        # Check calibration recommendations
        if "recommendations" in calibration:
            for rec in calibration["recommendations"]:
                if rec.get("priority") == "high":
                    recommendations.append({
                        "type": "calibration_needed",
                        "severity": rec.get("priority"),
                        "message": rec.get("issue"),
                        "action": rec.get("recommendation"),
                    })
        
        return {
            "model_version": model_version,
            "performance": performance,
            "calibration": calibration,
            "needs_refinement": needs_refinement,
            "recommendations": recommendations,
            "conversion_rate": conversion_rate,
            "threshold": min_acceptable_rate,
        }

    async def create_model_version(
        self,
        version: str,
        model_type: str,
        config: dict[str, Any],
        description: str | None = None,
    ) -> ModelVersion:
        """Create a new model version."""
        _logger.info("Creating model version", version=version, model_type=model_type)
        
        model_version = ModelVersion(
            version=version,
            model_type=model_type,
            config=config,
            status="draft",
            description=description,
        )
        
        self.session.add(model_version)
        await self.session.commit()
        await self.session.refresh(model_version)
        
        return model_version

    async def activate_model_version(self, version: str) -> ModelVersion:
        """Activate a model version for production use."""
        model_version = await self.session.execute(
            select(ModelVersion).where(ModelVersion.version == version)
        )
        model = model_version.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Model version {version} not found")
        
        # Deactivate current active version
        current_active = await self.session.execute(
            select(ModelVersion).where(ModelVersion.status == "active")
        )
        for active_model in current_active.scalars().all():
            active_model.status = "deprecated"
            active_model.deprecated_at = datetime.utcnow()
        
        # Activate new version
        model.status = "active"
        model.activated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(model)
        
        _logger.info("Model version activated", version=version)
        return model

    async def get_active_model_version(self) -> ModelVersion | None:
        """Get the currently active model version."""
        result = await self.session.execute(
            select(ModelVersion).where(ModelVersion.status == "active")
        )
        return result.scalar_one_or_none()

    async def automated_refinement_check(self) -> dict[str, Any]:
        """
        Automated check for model refinement needs.
        
        Should be run periodically (e.g., weekly) to detect performance issues.
        """
        _logger.info("Running automated refinement check")
        
        # Get active model
        active_model = await self.get_active_model_version()
        if not active_model:
            active_model_version = "v1.0"  # Default
        else:
            active_model_version = active_model.version
        
        # Check performance
        performance_check = await self.check_model_performance(
            model_version=active_model_version,
            min_feedback_count=50,
        )
        
        # Determine if action is needed
        action_needed = performance_check.get("needs_refinement", False) or len(
            performance_check.get("recommendations", [])
        ) > 0
        
        return {
            "check_time": datetime.utcnow().isoformat(),
            "active_model": active_model_version,
            "performance_check": performance_check,
            "action_needed": action_needed,
            "recommendations": performance_check.get("recommendations", []),
        }

